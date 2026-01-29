# Ported version of the C++ test application to Python 

#pip3 install dTwin
#pip3 install numpy
#pip3 install matplotlib

import os
import sys
import platform
from pathlib import Path
import dTwin
from dTwin import modelSolver

# Import the entire module
import plotTable
import matplotlib.pyplot as plt

print(dTwin.__doc__)        #Just to test 

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

#Author uses RAMDisk (Adjust your output location)
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

def testRealDynamic(problem: dTwin.DynamicProblem, in_fn: str, out_folder: str, t_final: float, param_name: str = '') -> str:
    p_log = dTwin.getConsoleLogger()
    p_model = dTwin.createRealDynamicModel(problem, p_log)
    if not p_model:
        print("ERROR! Cannot create model")
        return None

    in_file_name, out_file_name = get_in_out_file_names(in_fn, out_folder)
    if not in_file_name or not out_file_name:
        print("ERROR! Wrong input or output location!")
        return None

    if not p_model.initFromFile(in_file_name):
        print("ERROR! Cannot init from file!")
        return None

    p_dyn_solver = p_model.getSolverInterface()
    if not p_dyn_solver:
        print("ERROR! Cannot obtain solver interface!")
        return None

    with open(out_file_name, 'w', encoding='utf-8') as f_out:
        param_index = -1
        param_names = dTwin.StringVector(1)
        param_indices = dTwin.UintVector(1)
        param_values = dTwin.DoubleVector()

        if param_name:
            param_index = p_model.getParameterIndex(param_name)
            if param_index < 0:
                print(f"ERROR! Cannot find param='{param_name}' in model parameters")
                return None
            param_names[0] = param_name
            param_indices[0] = param_index
            param_values = p_model.getParameterValues(param_indices)
            # show_results(f_out, "Initial param values:", param_names, param_values)  # Uncomment if needed

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

        while t <= t_final:
            t += d_t
            if param_index >= 0:
                if 0.5 - eps_t <= t <= 0.5 + eps_t:
                    param_values[0] = -10
                    p_model.setParameterValues(param_indices, param_values)
                if 10 - eps_t <= t <= 10 + eps_t:
                    param_values[0] = -1
                    p_model.setParameterValues(param_indices, param_values)

            sol = p_dyn_solver.step()
            if sol != dTwin.Solution.OK:
                print("ERROR! Cannot solve the problem!")
                return None
            out_values = p_model.getOutputSymbolValues(out_indices)
            show_res_row(f_out, t, out_values)

    print("INFO! Dynamic test completed successfully!")
    return out_file_name

def testRealStatic(problem: dTwin.StaticProblem, in_fn: str, out_folder: str, param_name: str = '') -> str:
    p_log = dTwin.getConsoleLogger()
    p_model = dTwin.createRealStaticModel(problem, p_log)
    if not p_model:
        print("ERROR! Cannot create model")
        return None

    in_file_name, out_file_name = get_in_out_file_names(in_fn, out_folder)
    if not in_file_name or not out_file_name:
        print("ERROR! Wrong input or output location!")
        return None

    if not p_model.initFromFile(in_file_name):
        print("ERROR! Cannot init from file!")
        return None

    out_indices = p_model.getOutputSymbolIndices()
    if len(out_indices) == 0:
        print("ERROR! Cannot obtain output indices!")
        return None

    out_names = p_model.getOutputSymbolNames(out_indices)
    if len(out_names) == 0:
        print("ERROR! Cannot obtain output names!")
        return None

    p_static_solver = p_model.getSolverInterface()
    if not p_static_solver:
        print("ERROR! Cannot obtain solver interface!")
        return None

    with open(out_file_name, 'w', encoding='utf-8') as f_out:
        param_index = -1
        param_names = dTwin.StringVector(1)
        param_indices = dTwin.UintVector(1)
        param_values = dTwin.DoubleVector()

        if param_name:
            param_index = p_model.getParameterIndex(param_name)
            if param_index < 0:
                print(f"ERROR! Cannot find param='{param_name}' in model parameters")
                return None
            param_names[0] = param_name
            param_indices[0] = param_index
            param_values = p_model.getParameterValues(param_indices)
            show_results(f_out, "Initial param values:", param_names, param_values)

        sol = p_static_solver.solve()
        if sol != dTwin.Solution.OK:
            print("ERROR! Cannot solve the problem!")
            return None

        vals = p_model.getOutputSymbolValues(out_indices)
        show_results(f_out, "Output symbols for initial solution:", out_names, vals)

        if param_index < 0:
            print("INFO! Static test completed successfully (without parameter manipulation)!")
            return None

        param_values[0] -= 0.1
        p_model.setParameterValues(param_indices, param_values)
        show_results(f_out, "Updated param values:", param_names, param_values)

        sol = p_static_solver.solve()
        if sol != dTwin.Solution.OK:
            print("ERROR! Cannot solve the problem!")
            return None

        vals = p_model.getOutputSymbolValues(out_indices)
        show_results(f_out, "Output symbols for solution with updated params:", out_names, vals)

    print("INFO! Static test completed successfully!")
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
    str: New file path with label and new extension (e.g. "/path/to/file_freq.png")
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
    #Real static
    testRealStatic(dTwin.StaticProblem.NLE, get_modl_input("PF_PV_03.dmodl", Location.Real), outLocation, "P3_inj")

    #real dynamic (AC-gen with PI frequency regulaton)
    outFileName = testRealDynamic(dTwin.DynamicProblem.DAE, get_modl_input("FreqReg_01.dmodl", Location.Real), outLocation, 20.0, "P_l")
    if outFileName:
        fig1, ax1 = plotTable.plot(["f"], "t", file=outFileName, show=False)
        img1Name = replaceFileExtension(outFileName, "_f", ".png")
        fig1.savefig(img1Name)
        print(f"Created image: {img1Name}")
        fig2, ax2 = plotTable.plot(["P_gm", "P_ge", "regI"], "t", file=outFileName, show=False)
        img2Name = replaceFileExtension(outFileName, "_Pgm_Pge_regI", ".png")
        print(f"Created image: {img2Name}")
        fig2.savefig(img2Name)

    #disk with PD regulator
    outFileName = testRealDynamic(dTwin.DynamicProblem.DAE, get_modl_input("TF_Dorf_E760_PD_Disk_RK4.dmodl", Location.Real), outLocation, 0.5)
    if outFileName:
        fig3, ax3 = plotTable.plot(["y", "u", "err"], "t", file=outFileName, show=False)
        img3Name = replaceFileExtension(outFileName, "_PD", ".png")
        fig3.savefig(img3Name)
        print(f"Created image: {img3Name}")
    
    # Show all plots together
    plt.show()
