"""State machine for the calibration workflow.

This module provides a controller that manages the phase-based
calibration sequence, guiding the user through the process from
initial checks to final ICC profile generation.
"""
from enum import Enum, auto
import numpy as np
from . import analysis, config, icc


class CalibrationPhase(Enum):
    """Represents the sequential phases of the calibration process."""
    PRECONDITION = auto()
    PHASE_1_NEUTRAL_GREY = auto()
    PHASE_2_NEUTRAL_SLOPE = auto()
    PHASE_3_DRIVER_LOCK = auto()
    PHASE_4_COLOR_ANALYSIS = auto()
    PHASE_5_ICC_CONSTRUCTION = auto()
    COMPLETE = auto()
    ERROR = auto() # Added error state


class CalibrationController:
    """Manages the state and flow of the printer calibration process."""

    def __init__(self):
        self.phase = CalibrationPhase.PRECONDITION
        # History stores tuples of (measurement_df, adjustment_dict) for each step in phase 1
        self.history = []
        self.last_error_message = ""
        self.last_measurements_df = None # To store df from successful phase 4
        # Load configs
        self.phase1_targets = config.Phase1Targets()
        self.phase2_targets = config.Phase2Targets()
        self.phase4_targets = config.Phase4Targets()
        self.convergence_rules = config.Convergence()
        self.ink_steps = config.InkSteps()

    def get_current_phase(self) -> CalibrationPhase:
        """Returns the current calibration phase."""
        return self.phase

    def get_next_action(self) -> str:
        """Determines the next action for the user based on the current phase."""
        actions = {
            CalibrationPhase.PRECONDITION:
                "Verify preconditions (paper, ink, settings) and measure the neutral patches chart.",
            CalibrationPhase.PHASE_1_NEUTRAL_GREY:
                f"Calibrating mid-grey anchor ({self.phase1_targets.patch_name}). "
                "Apply the suggested adjustments and re-measure the neutral patches chart.",
            CalibrationPhase.PHASE_2_NEUTRAL_SLOPE:
                "Mid-grey anchor is calibrated. Now validating neutral slope with the same measurement data. No adjustments needed.",
            CalibrationPhase.PHASE_3_DRIVER_LOCK:
                "Driver adjustments are now locked. Do not change any driver color settings. "
                "Next, print and measure the full colour chart for analysis.",
            CalibrationPhase.PHASE_4_COLOR_ANALYSIS:
                "Analyzing full colour chart. This checks if the printer is within tolerance for ICC profiling.",
            CalibrationPhase.PHASE_5_ICC_CONSTRUCTION:
                "Printer is within tolerance. Go to the 'Export Profile' tab to save the ICC profile.",
            CalibrationPhase.COMPLETE:
                "Calibration is complete! ICC Profile has been generated.",
            CalibrationPhase.ERROR:
                f"An error occurred: {self.last_error_message}"
        }
        return actions.get(self.phase, "Calibration process is in an unhandled state.")

    def process_measurements(self, df):
        """Processes measurement data, provides suggestions, and updates the phase."""
        if self.phase == CalibrationPhase.PRECONDITION:
            self.phase = CalibrationPhase.PHASE_1_NEUTRAL_GREY
            # Fall through to immediately process the first measurement in Phase 1

        if self.phase == CalibrationPhase.PHASE_1_NEUTRAL_GREY:
            return self._process_phase1(df)
        elif self.phase == CalibrationPhase.PHASE_2_NEUTRAL_SLOPE:
             # Phase 2 uses the same data as the final step of phase 1
            return self._process_phase2(df)
        elif self.phase == CalibrationPhase.PHASE_4_COLOR_ANALYSIS:
            return self._process_phase4(df)
        elif self.phase in [CalibrationPhase.PHASE_3_DRIVER_LOCK, CalibrationPhase.COMPLETE, CalibrationPhase.PHASE_5_ICC_CONSTRUCTION]:
            self.last_error_message = "Driver adjustments are locked. No further measurements can be processed for tuning."
            return self.last_error_message
        else:
            return "No processing action defined for the current phase."

    def _process_phase1(self, df):
        """Handles the logic for Phase 1: mid-grey anchor calibration."""
        patch_name = self.phase1_targets.patch_name
        patch_lab = analysis.get_patch_lab(df, patch_name)

        if patch_lab is None:
            self.last_error_message = f"Patch '{patch_name}' not found in measurement data."
            self.phase = CalibrationPhase.ERROR
            return self.last_error_message

        current_err_val = self._get_phase1_error(patch_lab)
        is_converged = False

        if self.history:
            prev_df, _ = self.history[-1]
            prev_lab = analysis.get_patch_lab(prev_df, patch_name)

            if prev_lab and analysis.get_lab_distance(patch_lab, prev_lab) < self.convergence_rules.min_abs_change:
                is_converged = True

            prev_err_val = self._get_phase1_error(prev_lab)
            if current_err_val > prev_err_val:
                is_converged = True

        is_within_target = analysis.is_patch_within_target(patch_lab, self.phase1_targets)

        if is_converged:
            if is_within_target:
                self.history.append((df, {}))
                self.phase = CalibrationPhase.PHASE_2_NEUTRAL_SLOPE
                return self._process_phase2(df)
            else:
                self.phase = CalibrationPhase.PHASE_3_DRIVER_LOCK
                return "Phase 1 Converged but outside target. This may indicate driver limitations. Freezing adjustments."

        adjustment = analysis.suggest_adjustment(patch_lab, self.phase1_targets, self.ink_steps)
        self.history.append((df, adjustment))

        if not adjustment:
            if is_within_target:
                self.phase = CalibrationPhase.PHASE_2_NEUTRAL_SLOPE
                return self._process_phase2(df)
            else:
                self.last_error_message = "No effective adjustment could be calculated, but patch is not within target."
                self.phase = CalibrationPhase.ERROR
                return self.last_error_message

        return f"Suggestion for next print: {adjustment}"

    def _process_phase2(self, df):
        """Handles logic for Phase 2: neutral slope validation."""
        p1_patch_name = self.phase1_targets.patch_name
        p2_150_name = self.phase2_targets.rgb150_patch_name
        p2_200_name = self.phase2_targets.rgb200_patch_name

        p1_lab = analysis.get_patch_lab(df, p1_patch_name)
        p150_lab = analysis.get_patch_lab(df, p2_150_name)
        p200_lab = analysis.get_patch_lab(df, p2_200_name)

        if not all([p1_lab, p150_lab, p200_lab]):
            self.last_error_message = f"One or more neutral patches ({p1_patch_name}, {p2_150_name}, {p2_200_name}) are missing."
            self.phase = CalibrationPhase.ERROR
            return self.last_error_message

        p150_ok = (abs(p150_lab[1]) <= self.phase2_targets.rgb150_a_tol and
                   abs(p150_lab[2]) <= self.phase2_targets.rgb150_b_tol)
        p200_ok = (abs(p200_lab[1]) <= self.phase2_targets.rgb200_a_tol and
                   abs(p200_lab[2]) <= self.phase2_targets.rgb200_b_tol)

        if not (p150_ok and p200_ok):
            self.last_error_message = "Neutral slope validation failed. RGB150 or RGB200 are outside tolerance."
            self.phase = CalibrationPhase.ERROR
            return self.last_error_message

        p1_a_err, p1_b_err = p1_lab[1], p1_lab[2]
        p150_a_err, p150_b_err = p150_lab[1], p150_lab[2]
        p200_a_err, p200_b_err = p200_lab[1], p200_lab[2]

        if np.sign(p1_a_err) * np.sign(p150_a_err) < 0 or \
           np.sign(p150_a_err) * np.sign(p200_a_err) < 0 or \
           np.sign(p1_b_err) * np.sign(p150_b_err) < 0 or \
           np.sign(p150_b_err) * np.sign(p200_b_err) < 0:
            self.last_error_message = "Neutral slope is not monotonic. Indicates driver limits."
            self.phase = CalibrationPhase.PHASE_3_DRIVER_LOCK
            return f"{self.last_error_message} Freezing driver adjustments."

        self.phase = CalibrationPhase.PHASE_3_DRIVER_LOCK
        return "Phase 2 Passed: Neutral slope is valid. Driver adjustments are now locked."

    def _process_phase4(self, df):
        """Processes the full colour chart analysis for Phase 4."""
        passed, report = analysis.analyze_color_patches(df, self.phase4_targets)
        
        if passed:
            self.phase = CalibrationPhase.PHASE_5_ICC_CONSTRUCTION
            self.last_measurements_df = df # Save for export
        else:
            self.phase = CalibrationPhase.ERROR
            self.last_error_message = "Colour patch analysis failed. See report for details."
            
        return report

    def export_icc(self, filename: str) -> str:
        """Exports the ICC profile if in the correct phase."""
        if self.phase != CalibrationPhase.PHASE_5_ICC_CONSTRUCTION:
            return "Not in the correct phase to export an ICC profile."
        
        if self.last_measurements_df is None:
            self.phase = CalibrationPhase.ERROR
            self.last_error_message = "No valid measurement data available for export."
            return self.last_error_message

        ref_labs = analysis.get_reference_lab_values()
        success, message = icc.build_and_export_icc(
            self.last_measurements_df, ref_labs, filename
        )

        if success:
            self.phase = CalibrationPhase.COMPLETE
        
        return message

    def _get_phase1_error(self, patch_lab: tuple) -> float:
        """Calculates a simple scalar error for Phase 1 in the a*b* plane."""
        a_target = np.mean(self.phase1_targets.a_range)
        b_target = np.mean(self.phase1_targets.b_range)
        return np.sqrt((patch_lab[1] - a_target)**2 + (patch_lab[2] - b_target)**2)

    def get_rgb100_lab(self):
        """Convenience method to get the last measured RGB100 Lab values."""
        if not self.history:
            return None
        last_df, _ = self.history[-1]
        return analysis.get_patch_lab(last_df, self.phase1_targets.patch_name)

    def set_phase(self, phase: CalibrationPhase):
        """
        Advanced feature to manually set the calibration phase.
        This will reset the process history.
        """
        self.phase = phase
        self.history = []
        self.last_error_message = ""
        self.last_measurements_df = None

    def reset(self):
        """Resets the controller to its initial state."""
        self.set_phase(CalibrationPhase.PRECONDITION)
