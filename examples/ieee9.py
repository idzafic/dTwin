# Example with IEEE-9

#pip3 install dTwin
#pip3 install numpy
#pip3 install matplotlib

import os
import sys
import platform
from pathlib import Path
import time
import dTwin
from dTwin import modelSolver

# Import the entire module
import plotTable
import matplotlib.pyplot as plt

def get_in_out_file_names(in_file_name: str, out_folder: str) -> tuple[str, str]:
    if not out_folder:
        out_file_name = Path(in_file_name).with_suffix('.txt')
        if not out_file_name.exists():  # Note: C++ checks length, but here check if valid
            print(f"Input file name doesn't exist! Fn={in_file_name}")
            return '', ''
        return str(out_file_name), str(out_file_name)

    currentDir = Path(__file__).resolve().parent

    out_path: Path
    if out_folder.startswith('~'):
        home_path = Path.home()
        out_path = home_path / out_folder[1:].lstrip(os.sep)
    elif out_folder.startswith(':'):
        file_path = Path(in_file_name)
        #folder_path = file_path.parent
        #out_path = folder_path / out_folder[1:].lstrip(os.sep)
        out_path = currentDir / out_folder[1:].lstrip(os.sep)
        
    elif out_folder.startswith('.'):
        current_dir = Path.cwd()
        out_path = current_dir / out_folder[1:].lstrip(os.sep)
    else:
        out_path = Path(out_folder)

    file_path = Path(in_file_name)
    file_name = file_path.name
    fn = Path(file_name).with_suffix('.txt')
    out_path_with_file_name = out_path / fn
    out_path.mkdir(parents=True, exist_ok=True)
    out_file_name = str(out_path_with_file_name)

    # Assuming no syst::Environment::replaceVariablesInPath in Python, use as is
    in_file_name_wo_env_vars = in_file_name

    return in_file_name_wo_env_vars, out_file_name

# Enum for Location (as in C++)
class Location:
    Real = 0
    Complex = 1

def get_modl_input(file_name: str, location: int) -> str:
    home_path = Path.home()  # Assuming s_homePath is home
    currentDir = Path(__file__).resolve().parent
    if location == Location.Real:
        path = currentDir / "../models/real" / file_name
    elif location == Location.Complex:
        path = currentDir / "../models/cmplx" / file_name
    else:
        raise ValueError("Invalid location")
    return str(path)

def get_output(file_name: str) -> str:
    if sys.platform == 'win32':
        ram_disk = Path("R:/")
    elif sys.platform == "darwin":
        ram_disk = Path("/Volumes/RAMDisk")
    else:
        ram_disk = Path("/media/RAMDisk")
    path = ram_disk / file_name
    return str(path)

def show_results(f_out, lbl: str, out_names: dTwin.StringVector, vals: dTwin.DoubleVector):
    f_out.write("\n")
    f_out.write(lbl + "\n")
    f_out.write("--------------------\n")
    f_out.write("Name value\n")
    f_out.write("--------------------\n")
    for i in range(len(out_names)):
        f_out.write(f"{out_names[i]}: {vals[i]}\n")
    f_out.write("--------------------\n")

def show_res_header(f_out, out_names: dTwin.StringVector, lbl: str = None):
    if lbl:
        f_out.write(lbl + "\n")
    f_out.write("t")
    for name in out_names:
        f_out.write(f" {name}")
    f_out.write("\n")

def show_res_row(f_out, t: float, values: dTwin.DoubleVector):
    f_out.write(f"{t}")
    for val in values:
        f_out.write(f" {val}")
    f_out.write("\n")

def testIEE9Dynamics(problem: dTwin.DynamicProblem, in_fn: str, out_folder: str, t_final: float, pVar: str, qVar) -> str:
    p_log = dTwin.getConsoleLogger()
    p_model = dTwin.createRealDynamicModel(problem, p_log)
    if not p_model:
        print("ERROR! Cannot create model")
        return None

    in_file_name, out_file_name = get_in_out_file_names(in_fn, out_folder)
    if not in_file_name or not out_file_name:
        print("ERROR! Wrong input or output location!")
        return None

    start_time = time.perf_counter()
    if not p_model.initFromFile(in_file_name):
        print("ERROR! Cannot init from file!")
        return None
    
    end_time = time.perf_counter()

    elapsed_time = end_time - start_time
    print(f"Time required to load and init model: {elapsed_time:.6f} seconds")

    start_time = time.perf_counter()
    p_dyn_solver = p_model.getSolverInterface()
    if not p_dyn_solver:
        print("ERROR! Cannot obtain solver interface!")
        return None

    with open(out_file_name, 'w', encoding='utf-8') as f_out:
        param_index = -1
        param_names = dTwin.StringVector(2)
        param_indices = dTwin.UintVector(2)
        param_values = dTwin.DoubleVector()

        #get index of active power load variable that we want to manipulate
        param_index = p_model.getParameterIndex(pVar)
        if param_index < 0:
            print(f"ERROR! Cannot find param='{pVar}' in model parameters")
            return None
        param_names[0] = pVar
        param_indices[0] = param_index

        #get index of reactive power load variable that we want to manipulate
        param_index = p_model.getParameterIndex(qVar)
        if param_index < 0:
            print(f"ERROR! Cannot find param='{qVar}' in model parameters")
            return None
        param_names[1] = qVar
        param_indices[1] = param_index

        #get current parameter value for active and reactive power
        param_values = p_model.getParameterValues(param_indices)
        
        d_t = p_dyn_solver.getStepSize()
        if d_t <= 0:
            print("Warning! dTime was not initially specified. Default value is used-")
            d_t = 0.001
            p_dyn_solver.setStepSize(d_t)

        if not p_dyn_solver.reset(0):
            print("ERROR! Cannot reset the problem")
            return None

        out_indices = p_model.getOutputSymbolIndices()
        if len(out_indices) == 0:
            print("ERROR! Cannot obtain output indices!")
            return None

        out_names = p_model.getOutputSymbolNames(out_indices)
        if len(out_names) == 0:
            print("ERROR! Cannot obtain output names!")
            return None

        out_values = p_model.getOutputSymbolValues(out_indices)
        show_res_header(f_out, out_names)
        show_res_row(f_out, 0, out_values)

        t = 0.0
        eps_t = 1e-6
        #simulata some events at specific times
        while t <= t_final:
            t += d_t
            #first event happens at t=0.5 sec
            if 0.5 - eps_t <= t <= 0.5 + eps_t:
                #turn off load at node 5 (this could be real time event)
                param_values[0] = 0     #equivalent to P_load5=0
                param_values[1] = 0     #equivalent to Q_load5=0
                #update model with new params
                p_model.setParameterValues(param_indices, param_values)
            #at t=6 sec we turn the load on again
            if 6 - eps_t <= t <= 6 + eps_t:
                #turn on load at node 5
                param_values[0] = 1.25     #equivalent to P_load5=1.25
                param_values[1] = 0.5    #equivalent to Q_load5=0.5
                #update model with new params
                p_model.setParameterValues(param_indices, param_values)

            sol = p_dyn_solver.step()
            if sol != dTwin.Solution.OK:
                print("ERROR! Cannot solve the problem!")
                return None
            out_values = p_model.getOutputSymbolValues(out_indices)
            show_res_row(f_out, t, out_values)

    end_time = time.perf_counter()

    elapsed_time = end_time - start_time
    print(f"Time required to simulate {t_final} seconds of DAE model and write results in files: {elapsed_time:.6f} seconds")

    print("INFO! Dynamic test completed successfully!")
    return out_file_name

def getOutLocation() -> str:
    """
    Returns RAMDisk path if it exists, otherwise returns the location
    of Path(__file__) / "Res".
    """
    # Get the directory of the current file
    current_file_dir = Path(__file__).parent
    fallback_path = current_file_dir / "ResPy"
    
    # Define RAMDisk paths for each system
    system = platform.system()
    
    ramdisk_paths = []
    if system == "Windows":
        ramdisk_paths = ["R:/", "Z:/"]
    elif system == "Darwin":  # macOS
        ramdisk_paths = ["/Volumes/RAMDisk", "/tmp/RAMDisk"]
    else:               #"Linux", "Unix":
        ramdisk_paths = ["/media/RAMDisk", "/mnt/RAMDisk", "/tmp/RAMDisk"]
    
    
    # Check each RAMDisk path
    for ramdisk_path in ramdisk_paths:
        if os.path.exists(ramdisk_path):
            # Convert string path to Path object for proper concatenation
            return str(Path(ramdisk_path) / "ResPy")
    
    # If no RAMDisk exists, return the fallback path
    return str(fallback_path)

#file name manipulations
def replaceFileExtension(inputName: str, label: str, extension: str) -> str:
    """
    Replace or add file extension with a label.
    
    Parameters:
    -----------
    inputName : str
        Input file path (e.g., "/path/to/file.xml")
    label : str
        Label to insert before the extension (e.g., "_freq")
    extension : str
        New extension without dot (e.g., "png")
    
    Returns:
    --------
    str: New file path with label and new extension
    -------
    """
    # Create Path object
    path = Path(inputName)
    
    # Get stem (filename without extension)
    stem = path.stem
    
    # Add label to stem
    new_stem = f"{stem}{label}"
    
    # Create new path with new extension
    new_path = path.with_name(f"{new_stem}.{extension.lstrip('.')}")
    
    return str(new_path)

if __name__ == "__main__":
    # Solve and interact static and dynamic problems

    #get results (output) location
    outLocation = getOutLocation()
    #real dynamic (AC-gen with PI frequency regulaton)
    outFileName = testIEE9Dynamics(dTwin.DynamicProblem.DAE, get_modl_input("IEEE9_3Gens.dmodl", Location.Real), outLocation, 12.0, "P_load5", "Q_load5")
    if outFileName:
        fig1, ax1 = plotTable.plot(["P_gm_g1", "Pe_g1", "P_gm_g2", "Pe_g2", "P_gm_g3", "Pe_g3"], "t", file=outFileName, show=False)
        img1Name = replaceFileExtension(outFileName, "_Ps", ".png")
        fig1.savefig(img1Name)
        print(f"Created image: {img1Name}")
        fig2, ax2 = plotTable.plot(["V_t_g1", "V_t_g2", "V_t_g3"], "t", file=outFileName, show=False)
        img2Name = replaceFileExtension(outFileName, "_Vs", ".png")
        print(f"Created image: {img2Name}")
        fig2.savefig(img2Name)
    
    # Show all plots together
    plt.show()
