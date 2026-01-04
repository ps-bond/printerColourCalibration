"""ICC profile utilities.

This module contains helpers to create or save ICC profiles.
The main function `build_and_export_icc` serves as a placeholder to
demonstrate the final step of the calibration workflow.
"""
import pandas as pd

def build_and_export_icc(
    measurements_df: pd.DataFrame, 
    reference_labs: dict, 
    filename: str
) -> tuple[bool, str]:
    """
    Builds a placeholder ICC profile and exports it to a file.

    This function simulates the process of creating an ICC profile LUT
    from measured and reference Lab values. It does not create a real,
    usable ICC profile but generates a text file containing the mapping
    which represents the result of the calibration.

    Parameters
    ----------
    measurements_df : pd.DataFrame
        DataFrame containing the measured patch data, including 'patch', 'L', 'a', 'b'.
    reference_labs : dict
        Dictionary of reference Lab values with patch names as keys.
    filename : str
        The path to save the placeholder ICC profile to.

    Returns
    -------
    tuple[bool, str]
        A tuple containing a boolean success status and a message.
    """
    if not filename.lower().endswith(".icc"):
        filename += ".icc"

    try:
        with open(filename, "w") as f:
            f.write("# Placeholder ICC Profile\n")
            f.write("# This is not a valid ICC file. It contains the data mapping from the calibration process.\n\n")
            f.write("patch_name,measured_L,measured_a,measured_b,reference_L,reference_a,reference_b\n")

            for _, row in measurements_df.iterrows():
                patch_name = row['patch']
                if patch_name in reference_labs:
                    ref_lab = reference_labs[patch_name]
                    f.write(
                        f"{patch_name},{row['L']:.2f},{row['a']:.2f},{row['b']:.2f},"
                        f"{ref_lab[0]:.2f},{ref_lab[1]:.2f},{ref_lab[2]:.2f}\n"
                    )
        
        return True, f"Successfully exported placeholder ICC profile to {filename}"

    except Exception as e:
        return False, f"Failed to export ICC profile: {e}"
