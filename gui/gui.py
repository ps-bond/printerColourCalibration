'''
A Qt6-based GUI for the printer calibration tools.

To run this GUI, you need PyQt6:
pip install PyQt6
'''
import sys
import os
import pandas as pd
from functools import partial

# This is to ensure the printer_calibration module can be found when running this script directly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

__version__ = "0.5.0"

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
        QFormLayout, QGroupBox, QLabel, QLineEdit, QPushButton,
        QMessageBox, QFileDialog, QTextEdit, QHBoxLayout, QTableWidget, QDialog,
        QTableWidgetItem, QHeaderView, QComboBox, QStyledItemDelegate
    )
    from PyQt6.QtGui import QAction, QDoubleValidator
    from PyQt6.QtCore import Qt
except ImportError:
    print("PyQt6 is not installed. Please install it using: pip install PyQt6")
    sys.exit(1)

try:
    from printer_calibration import charts, io, config
    from printer_calibration.controller import CalibrationController, CalibrationPhase
except ImportError as e:
    print(f"Could not import 'printer_calibration' module: {e}")
    print("Please ensure you are running this from the project's root directory.")
    sys.exit(1)


# The a* and b* channels in CIELAB are theoretically unbounded, but in practice
# a range of -128 to 127 is used by many applications, including Photoshop.
class LabValueDelegate(QStyledItemDelegate):
    """A delegate for validating L*, a*, b* values in the table."""
    def __init__(self, min_val, max_val, parent=None):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        # Validator for float with 2 decimal places in the specified range.
        validator = QDoubleValidator(self.min_val, self.max_val, 2, editor)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        editor.setValidator(validator)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setText(str(value))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text(), Qt.ItemDataRole.EditRole)




class ChartsTab(QWidget):
    """Tab for generating calibration charts."""
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        neutral_group_box = QGroupBox("Neutral Chart")
        neutral_layout = QFormLayout()
        self.neutral_file_input = QLineEdit("neutral_chart_A4.pdf")
        neutral_layout.addRow("Filename:", self.neutral_file_input)
        generate_neutral_button = QPushButton("Generate")
        generate_neutral_button.clicked.connect(self.generate_neutral_chart)
        neutral_layout.addRow(generate_neutral_button)
        neutral_group_box.setLayout(neutral_layout)
        main_layout.addWidget(neutral_group_box)

        colour_group_box = QGroupBox("Colour Chart")
        colour_layout = QFormLayout()
        self.colour_file_input = QLineEdit("colour_test_A4.pdf")
        colour_layout.addRow("Filename:", self.colour_file_input)
        generate_colour_button = QPushButton("Generate")
        generate_colour_button.clicked.connect(self.generate_colour_chart)
        colour_layout.addRow(generate_colour_button)
        colour_group_box.setLayout(colour_layout)
        main_layout.addWidget(colour_group_box)

    def generate_neutral_chart(self):
        filename = self.neutral_file_input.text().strip()
        if not filename:
            QMessageBox.warning(self, "Invalid Filename", "Filename cannot be empty.")
            return
        if not filename.endswith(".pdf"):
            QMessageBox.warning(self, "Invalid Filename", "Filename must end with .pdf")
            return
        try:
            charts.generate_neutral_chart(filename, format="PDF")
            QMessageBox.information(self, "Success", f"Successfully generated {filename}")
        except PermissionError:
             QMessageBox.critical(self, "Error", f"Could not write to file '{filename}'. It might be open in another program.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate chart:\n{e}")

    def generate_colour_chart(self):
        filename = self.colour_file_input.text().strip()
        if not filename:
            QMessageBox.warning(self, "Invalid Filename", "Filename cannot be empty.")
            return
        if not filename.endswith(".pdf"):
            QMessageBox.warning(self, "Invalid Filename", "Filename must end with .pdf")
            return
        try:
            charts.generate_colour_chart(filename, format="PDF")
            QMessageBox.information(self, "Success", f"Successfully generated {filename}")
        except PermissionError:
             QMessageBox.critical(self, "Error", f"Could not write to file '{filename}'. It might be open in another program.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate chart:\n{e}")


class AnalysisTab(QWidget):
    """A unified tab for data entry, file I/O, and analysis."""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.controller = main_window.controller
        self.current_chart_type = None
        
        main_layout = QVBoxLayout(self)

        # --- Data Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Patch", "L*", "a*", "b*"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        
        # --- Set delegates for validation ---
        self.l_delegate = LabValueDelegate(0.0, 100.0, self)
        self.ab_delegate = LabValueDelegate(-128.0, 127.0, self)
        self.table.setItemDelegateForColumn(1, self.l_delegate)
        self.table.setItemDelegateForColumn(2, self.ab_delegate)
        self.table.setItemDelegateForColumn(3, self.ab_delegate)
        
        main_layout.addWidget(self.table)

        # --- Action Buttons ---
        button_layout = QHBoxLayout()
        load_button = QPushButton("Load from CSV...")
        load_button.clicked.connect(self.load_from_csv)
        save_button = QPushButton("Save to CSV...")
        save_button.clicked.connect(self.save_to_csv)
        process_button = QPushButton("Process Measurements")
        process_button.clicked.connect(self.process_data_from_table)
        
        button_layout.addWidget(load_button)
        button_layout.addWidget(save_button)
        button_layout.addStretch()
        button_layout.addWidget(process_button)
        main_layout.addLayout(button_layout)

        self.populate_table()

    def get_chart_type(self):
        """Determines the chart type based on the current calibration phase."""
        phase = self.controller.get_current_phase()
        if phase in [CalibrationPhase.PHASE_4_COLOR_ANALYSIS, CalibrationPhase.PHASE_5_ICC_CONSTRUCTION, CalibrationPhase.COMPLETE]:
            return "Colour"
        return "Neutral"

    def update_ui_for_phase(self):
        """Adjusts the chart type selection based on the current calibration phase."""
        # Ensure the table is populated correctly after UI update
        self.populate_table()

    def populate_table(self):
        """Fills the 'Patch' column with names based on the selected chart type."""
        chart_type = self.get_chart_type()
        
        # If the chart type hasn't changed, do not clear the table data
        if self.current_chart_type == chart_type:
            return
        self.current_chart_type = chart_type

        patches = config.NEUTRAL_PATCHES if chart_type == "Neutral" else config.COLOUR_PATCHES
        
        self.table.setRowCount(len(patches))
        for i, patch_info in enumerate(patches):
            name = patch_info[0]
            patch_item = QTableWidgetItem(name)
            # Make patch name non-editable and non-selectable for tabbing
            patch_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(i, 0, patch_item)
            for j in range(1, 4): # Clear L, a, b columns
                self.table.setItem(i, j, QTableWidgetItem(""))

    def get_dataframe_from_table(self) -> pd.DataFrame | None:
        """Reads the content of the QTableWidget and returns it as a DataFrame."""
        rows = self.table.rowCount()
        data = []
        for i in range(rows):
            try:
                patch_item = self.table.item(i, 0)
                l_item = self.table.item(i, 1)
                
                if not (patch_item and l_item and l_item.text()):
                    continue

                patch = patch_item.text()
                l_val = float(l_item.text())
                a_val = float(self.table.item(i, 2).text())
                b_val = float(self.table.item(i, 3).text())
                data.append({'patch': patch, 'L': l_val, 'a': a_val, 'b': b_val, 'rgb': 'N/A'})

            except (ValueError, AttributeError) as e:
                QMessageBox.warning(self, "Invalid Data", f"Please enter valid numbers for all fields in row {i+1} for patch {patch}.\nError: {e}")
                return None
        
        if not data:
            QMessageBox.warning(self, "No Data", "No valid measurement data was entered in the table.")
            return None
            
        return pd.DataFrame(data)

    def process_data_from_table(self):
        """Gets data from the table and tells the main window to process it."""
        df = self.get_dataframe_from_table()
        if df is not None:
            self.main_window.process_dataframe(df)

    def load_from_csv(self):
        """Loads data from a CSV file, validates it, and populates the table."""
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Measurement File", "", "CSV Files (*.csv);;All Files (*)")
        if not filepath:
            return

        try:
            loaded_df = io.load_csv(filepath)
            
            # --- Validation ---
            chart_type = self.get_chart_type()
            expected_patches_list = config.NEUTRAL_PATCHES if chart_type == "Neutral" else config.COLOUR_PATCHES
            expected_patch_names = {p[0] for p in expected_patches_list}
            loaded_patch_names = set(loaded_df['patch'].astype(str))

            missing_patches = expected_patch_names - loaded_patch_names
            extra_patches = loaded_patch_names - expected_patch_names

            if missing_patches:
                QMessageBox.warning(self, "Missing Patches", f"The loaded file is missing the following expected patches for a '{chart_type}' chart:\n\n" + "\n".join(sorted(missing_patches)))
            
            if extra_patches:
                QMessageBox.information(self, "Extra Patches", f"The loaded file contains extra patches not defined for a '{chart_type}' chart:\n\n" + "\n".join(sorted(extra_patches)))

            # --- Populate Table ---
            self.current_chart_type = None  # Force table refresh
            self.populate_table() # Reset table to expected structure
            
            data_dict = {str(row['patch']): (row['L'], row['a'], row['b']) for _, row in loaded_df.iterrows()}
            
            for i in range(self.table.rowCount()):
                patch_name = self.table.item(i, 0).text()
                if patch_name in data_dict:
                    lab = data_dict[patch_name]
                    self.table.setItem(i, 1, QTableWidgetItem(f"{lab[0]:.2f}"))
                    self.table.setItem(i, 2, QTableWidgetItem(f"{lab[1]:.2f}"))
                    self.table.setItem(i, 3, QTableWidgetItem(f"{lab[2]:.2f}"))
            
            self.main_window.results_text.append(f"Loaded and validated {os.path.basename(filepath)}.")

        except Exception as e:
            QMessageBox.critical(self, "Error Loading File", f"Could not load or parse the CSV file:\n{e}")

    def save_to_csv(self):
        """Saves the data from the table to a CSV file."""
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Measurements", "", "CSV Files (*.csv);;All Files (*)")
        if not filepath:
            return

        df = self.get_dataframe_from_table()
        if df is not None:
            try:
                df_to_save = df[['patch', 'rgb', 'L', 'a', 'b']]
                df_to_save.to_csv(filepath, index=False)
                QMessageBox.information(self, "Success", f"Successfully saved measurements to {os.path.basename(filepath)}.")
            except Exception as e:
                QMessageBox.critical(self, "Error Saving File", f"Could not save the file:\n{e}")


class ExportTab(QWidget):
    """Tab for exporting ICC profiles."""
    # This class remains unchanged from the previous version
    def __init__(self, controller: CalibrationController, main_window):
        super().__init__()
        self.controller = controller
        self.main_window = main_window

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        export_group = QGroupBox("Export ICC Profile")
        export_layout = QVBoxLayout()
        
        self.info_label = QLabel("Once calibration is passed (Phase 5), you can export the profile here.")
        self.info_label.setWordWrap(True)
        export_layout.addWidget(self.info_label)

        file_path_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select a location to save the ICC profile...")
        self.save_as_button = QPushButton("Save As...")
        self.save_as_button.clicked.connect(self.browse_save_location)
        file_path_layout.addWidget(self.file_path_input)
        file_path_layout.addWidget(self.save_as_button)
        export_layout.addLayout(file_path_layout)
        
        self.export_button = QPushButton("Export ICC Profile")
        self.export_button.clicked.connect(self.export_icc)
        export_layout.addWidget(self.export_button)

        export_group.setLayout(export_layout)
        main_layout.addWidget(export_group)
        
        # Initialize state
        self.update_ui_state(self.controller.get_current_phase())

    def update_ui_state(self, phase: CalibrationPhase):
        """Updates the enabled state of the export controls based on the phase."""
        is_ready = phase in [CalibrationPhase.PHASE_5_ICC_CONSTRUCTION, CalibrationPhase.COMPLETE]
        self.export_button.setEnabled(is_ready)
        self.file_path_input.setEnabled(is_ready)
        self.save_as_button.setEnabled(is_ready)
        
        if is_ready:
            self.info_label.setText("Calibration data ready. You can now export the ICC profile.")
            if not self.file_path_input.text():
                self.file_path_input.setText("printer_profile.icc")
        else:
            self.info_label.setText("Please complete the calibration analysis (Phase 4) before exporting.")

    def browse_save_location(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save ICC Profile", "", "ICC Profile (*.icc);;All Files (*)")
        if filename:
            self.file_path_input.setText(filename)
    
    def export_icc(self):
        filename = self.file_path_input.text()
        if not filename:
            QMessageBox.warning(self, "No Filename", "Please specify a filename for the ICC profile.")
            return
        
        try:
            message = self.controller.export_icc(filename)
            QMessageBox.information(self, "Export Status", message)
            self.main_window.update_status_display()
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export ICC profile:\n{e}")


class MainWindow(QMainWindow):
    """Main application window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Printer Calibration GUI v{__version__}")
        self.setGeometry(100, 100, 800, 600)

        self.controller = CalibrationController()
        
        # Main layout
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Left side: Tabs for actions
        self.tab_widget = QTabWidget()
        self.charts_tab = ChartsTab()
        self.analysis_tab = AnalysisTab(self)
        self.export_tab = ExportTab(self.controller, self)
        
        self.tab_widget.addTab(self.charts_tab, "1. Generate Charts")
        self.tab_widget.addTab(self.analysis_tab, "2. Analysis")
        self.tab_widget.addTab(self.export_tab, "3. Export Profile")
        main_layout.addWidget(self.tab_widget, 1)

        # Right side: Status and Results
        status_results_widget = QWidget()
        status_results_layout = QVBoxLayout(status_results_widget)
        
        status_group = QGroupBox("Calibration Status")
        status_layout = QFormLayout()
        self.phase_label = QLabel()
        self.action_label = QLabel()
        self.action_label.setWordWrap(True)
        status_layout.addRow("Current Phase:", self.phase_label)
        status_layout.addRow("Next Action:", self.action_label)
        status_group.setLayout(status_layout)
        status_results_layout.addWidget(status_group)

        results_group = QGroupBox("Results Log")
        results_layout = QVBoxLayout(results_group)
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        status_results_layout.addWidget(results_group)
        main_layout.addWidget(status_results_widget, 1)

        self._create_menus()
        self.update_status_display()
        self.analysis_tab.update_ui_for_phase()

    def process_dataframe(self, df):
        """The single point for processing a dataframe and updating the UI."""
        if df is None or df.empty:
            self.results_text.append("Cannot process empty measurement data.")
            return

        result_message = self.controller.process_measurements(df)
        self.results_text.append(f"Controller: {result_message}\n")
        self.update_status_display()

    def update_status_display(self):
        phase = self.controller.get_current_phase()
        self.phase_label.setText(str(phase))
        self.action_label.setText(self.controller.get_next_action())
        self.tab_widget.setTabEnabled(2, True)
        self.export_tab.update_ui_state(phase)
        self.analysis_tab.update_ui_for_phase()
        
        if phase == CalibrationPhase.PHASE_3_DRIVER_LOCK:
            self.controller.set_phase(CalibrationPhase.PHASE_4_COLOR_ANALYSIS)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self.update_status_display)
        elif phase in [CalibrationPhase.PHASE_5_ICC_CONSTRUCTION, CalibrationPhase.COMPLETE]:
            # Automatically switch to the Export Profile tab when ready to export
            self.tab_widget.setCurrentIndex(2)

    def _create_menus(self):
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")
        save_action = QAction("&Save Calibration", self)
        save_action.triggered.connect(self.save_profile)
        file_menu.addAction(save_action)

        load_action = QAction("&Load Calibration", self)
        load_action.triggered.connect(self.load_profile)
        file_menu.addAction(load_action)

        file_menu.addSeparator()

        exit_action = QAction("&Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        self._create_advanced_menu()

        help_menu = menu_bar.addMenu("&Help")
        instructions_action = QAction("&Instructions", self)
        instructions_action.triggered.connect(self.show_instructions_dialog)
        help_menu.addAction(instructions_action)

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def _create_advanced_menu(self):
        advanced_menu = self.menuBar().addMenu("&Advanced")
        
        reset_action = QAction("Reset Calibration", self)
        reset_action.triggered.connect(self.reset_calibration)
        advanced_menu.addAction(reset_action)

        skip_menu = advanced_menu.addMenu("Skip to Phase...")
        for phase in CalibrationPhase:
            if phase not in [CalibrationPhase.COMPLETE, CalibrationPhase.ERROR]:
                action = QAction(str(phase), self)
                action.triggered.connect(partial(self.skip_to_phase, phase))
                skip_menu.addAction(action)

    def reset_calibration(self):
        self.controller.reset()
        self.results_text.clear()
        self.results_text.append("--- CALIBRATION RESET ---\n")
        self.analysis_tab.current_chart_type = None  # Force table clear
        self.update_status_display()

    def save_profile(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Calibration Profile", "", "Calibration Profile (*.cal);;All Files (*)")
        if filepath:
            try:
                self.controller.save_state(filepath)
                QMessageBox.information(self, "Success", f"Calibration profile saved to {os.path.basename(filepath)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save calibration profile:\n{e}")

    def load_profile(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Load Calibration Profile", "", "Calibration Profile (*.cal);;All Files (*)")
        if filepath:
            try:
                loaded_controller = CalibrationController.load_state(filepath)
                self.controller = loaded_controller
                self.results_text.append(f"\n--- PROFILE LOADED FROM {os.path.basename(filepath)} ---\n")
                self.update_status_display()
                # Ensure all tabs are updated with the new controller
                self.analysis_tab.controller = self.controller
                self.export_tab.controller = self.controller
                self.analysis_tab.update_ui_for_phase()
                self.tab_widget.setCurrentIndex(self.tab_widget.indexOf(self.analysis_tab)) # Switch to analysis tab after loading
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load calibration profile:\n{e}")

    def skip_to_phase(self, phase: CalibrationPhase):
        self.controller.set_phase(phase)
        self.results_text.append(f"\n--- SKIPPED TO {phase.name} ---\n")
        self.update_status_display()

    def show_instructions_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Calibration Instructions")
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("font-size: 12pt;")
        text_edit.setHtml(
            """<p><b>Printer Calibration & ICC Profiling Workflow</b></p>
            <p>
            This process calibrates your printer, ink, paper, and driver settings as a single fixed system,
            then builds an ICC profile to correct the remaining colour error.
            Do not skip steps or change settings mid-process.
            </p>

            <ol>
            <li>
            <b>Stage 0 — Preparation (Required)</b>
            <ul>
            <li>Select the correct printer, paper type, and print quality in the driver.</li>
            <li>Create and select a <b>named driver preset</b> containing all current settings.</li>
            <li>Disable any automatic enhancements (auto colour, vivid mode, sharpening, etc.).</li>
            <li>Ensure the printer has been idle for at least 10 minutes.</li>
            <li>Ensure prints will be allowed to dry for <b>at least 2 hours</b> (overnight preferred).</li>
            </ul>
            <i>All calibration depends on the driver preset remaining unchanged for the entire process.</i>
            </li>
            <br />
            <li>
            <b>Stage 1 — Print Neutral Tone Test Chart</b>
            <ul>
            <li>Print the neutral grey test chart using the selected driver preset.</li>
            <li>Do not apply any ICC profile at this stage.</li>
            <li>Allow the print to dry fully before measurement.</li>
            </ul>
            <i>This chart is used to stabilise the printer’s neutral behaviour.</i>
            </li>
            <br />
            <li>
            <b>Stage 2 — Mid-Grey Neutral Anchor (RGB100)</b>
            <ul>
            <li>Measure the RGB100 grey patch using your colour measurement device.</li>
            <li>Adjust the driver CMY sliders to reduce colour cast in this patch.</li>
            <li>Target values (approximate):
              <ul>
                <li>L* ≈ 38 (±2)</li>
                <li>a* within ±2</li>
                <li>b* within ±4</li>
              </ul>
            </li>
            <li>Reprint the chart and re-measure after each adjustment.</li>
            <li>Stop adjusting when changes no longer meaningfully reduce error.</li>
            </ul>
            <i>This is a coarse correction only. Do not chase perfection.</i>
            </li>
            <br />
            <li>
            <b>Stage 3 — Neutral Linearity Validation (RGB150, RGB200)</b>
            <ul>
            <li>Measure additional neutral patches (RGB150 and RGB200).</li>
            <li>Verify that:
              <ul>
                <li>Colour error decreases toward highlights</li>
                <li>No strong colour cast appears in lighter greys</li>
              </ul>
            </li>
            <li>If highlights worsen while mid-grey improves, stop adjusting the driver.</li>
            <li>Once acceptable, <b>freeze the driver settings</b>.</li>
            </ul>
            <i>From this point onward, driver sliders must not be changed.</i>
            </li>
            <br />
            <li>
            <b>Stage 4 — Print and Measure Colour Chart</b>
            <ul>
            <li>Print the full colour test chart using the frozen driver preset.</li>
            <li>Ensure colour management is disabled for printing the chart.</li>
            <li>Allow the print to dry fully.</li>
            <li>Measure all colour patches in the specified order.</li>
            </ul>
            <i>This data characterises the printer’s full colour behaviour.</i>
            </li>
            <br />
            <li>
            <b>Stage 5 — ICC Profile Generation</b>
            <ul>
            <li>Process the measured colour data.</li>
            <li>Generate an ICC profile that corrects remaining colour and tone errors.</li>
            <li>Save the profile with a name matching the driver preset.</li>
            </ul>
            <i>The ICC profile assumes the driver preset remains unchanged.</i>
            </li>
            <br />
            <li>
            <b>Stage 6 — Validation (Strongly Recommended)</b>
            <ul>
            <li>Print a validation chart using the new ICC profile.</li>
            <li>Measure the patches and verify ΔE values are within acceptable limits.</li>
            <li>Confirm neutral greys are visually neutral.</li>
            </ul>
            <i>If validation fails, the ICC profile should not be used.</i>
            </li>
            </ol>
            <br />
            <p>
            <b>Important:</b> If you change paper, ink, print quality, or driver sliders,
            you must repeat the entire calibration process and generate a new ICC profile.
            </p>"""
        )
        layout.addWidget(text_edit)

        dialog.exec()

    def show_about_dialog(self):
        QMessageBox.about(
            self,
            "About Printer Calibration GUI",
            f"""<p><b>Printer Calibration GUI v{__version__}</b></p>
            <p>A tool to help calibrate printer colour balance and generate an ICC profile.</p>
            <p>This application guides you through measuring printed charts and suggests
            adjustments to your printer's driver settings to achieve more accurate
            colour reproduction.</p>"""
        )

def cli():
    """Entrypoint for the GUI."""
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    cli()