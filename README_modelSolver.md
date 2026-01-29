# dTwin

**dTwin** is a Python interface to a high‑performance C++ nonlinear model solver capable of solving:

* **Static problems**
  * Nonlinear algebraic equations (NLE)
  * Weighted Least Squares (WLS)
  
* **Dynamic problems**
  * Ordinary Differential Equations (ODE)
  * Nonlinear Differential‑Algebraic Equations (DAE)

It is built using the C++ `modelSolver` library (part of the *dTwin* framework).

This README explains how to **install**, **understand**, and **use** `dTwin` step by step, with real working examples.

---

## 1. Installation

### Install from official Python repository

```bash
pip install dTwin
```

### Verify installation

```python
import dTwin
from dTwin import modelSolver
print(dTwin.__doc__)
```

---

## 2. What does dTwin.modelSolver solve?

| Problem type  | Description                              |
| ------------- | ---------------------------------------- |
| Static (NLE)  | Systems of nonlinear algebraic equations |
| Static (WLS)  | Weighted least squares estimation        |
| Dynamic (ODE) | Time‑domain simulation of ODE systems    |
| Dynamic (DAE) | Time‑domain simulation of nonlinear DAEs |

Models are described using **`.dmodl` files**, a domain‑specific language for defining variables, parameters, equations, limits, controllers, and submodels.

---

## 3. Core Python API overview

### Enumerations

```python
dTwin.StaticProblem.NLE
dTwin.StaticProblem.WLS

dTwin.DynamicProblem.ODE
dTwin.DynamicProblem.DAE

dTwin.Solution.OK
```

### Vector types (C++ backed)

These are zero‑copy wrappers around C++ memory:

```python
dTwin.DoubleVector
dTwin.StringVector
dTwin.UintVector
```

They behave like Python vectors:

```python
v = dTwin.DoubleVector(3)
v[0] = 1.0
print(len(v), v)
```

---
##4. Examples

There are several examples in the **examples** subfolder.
Example models are located in **models** subfolder.

### 4.1 Static model example (Power‑flow NLE)

### Model file: `PF_PV_03.dmodl`

This model solves a **power‑flow problem** with:

* PV and PQ buses
* Generator voltage regulation (PV node with limits)
* Reactive power limits

(Details: see associated arXiv paper.)

### Python usage

```python
import dTwin
from pathlib import Path

p_log = dTwin.getConsoleLogger()

# Create real‑valued static model (NLE)
p_model = dTwin.createRealStaticModel(
    dTwin.StaticProblem.NLE,
    p_log
)

# Load model
p_model.initFromFile("PF_PV_03.dmodl")

# Obtain solver
p_solver = p_model.getSolverInterface()

# Solve
status = p_solver.solve()
assert status == dTwin.Solution.OK

# Extract outputs
out_indices = p_model.getOutputSymbolIndices()
out_names   = p_model.getOutputSymbolNames(out_indices)
out_values  = p_model.getOutputSymbolValues(out_indices)

for i in range(len(out_names)):
    print(out_names[i], out_values[i])

p_model.release()
```

### Parameter manipulation

```python
idx = p_model.getParameterIndex("P3_inj")
vals = p_model.getParameterValues(dTwin.UintVector([idx]))
vals[0] -= 0.1
p_model.setParameterValues(dTwin.UintVector([idx]), vals)

p_solver.solve()
```

---
### 4.2 Dynamic DAE example (Generator frequency regulation)

### Model file: `FreqReg_01.dmodl`

This model simulates:

* Synchronous generator swing equation
* PI frequency controller
* Nonlinear network algebraic equations
* Initial power‑flow solved via a **SubModel**
* Fully nonlinear time‑domain simulation

### Python usage

```python
import dTwin

p_log = dTwin.getConsoleLogger()

p_model = dTwin.createRealDynamicModel(
    dTwin.DynamicProblem.DAE,
    p_log
)

p_model.initFromFile("FreqReg_01.dmodl")

p_solver = p_model.getSolverInterface()

# Time step (optional)
dt = p_solver.getStepSize()
if dt <= 0:
    p_solver.setStepSize(0.001)    

# Initialize
p_solver.reset(0.0)

out_idx   = p_model.getOutputSymbolIndices()
out_names = p_model.getOutputSymbolNames(out_idx)

# Time loop
t = 0.0
T_END = 20.0

while t <= T_END:
    #change model parameter to simulate transients
    sol = p_solver.step()
    assert sol == dTwin.Solution.OK

    values = p_model.getOutputSymbolValues(out_idx)
    print(t, list(values))
    t += dt

p_model.release()
```

---

### 4.3 Dynamic model with transfer functions (Dorf's example)

### Model file: `TF_Dorf_E760_PD_Disk_RK4.dmodl`.

Features:

* Laplace transfer functions (`TFs`)
* PID (PD) controller
* Implicit RK4/RK6 integration

No Python code changes are required — simply load the model and simulate as shown above.

---

## 5. Memory management (important)

Models are C++ objects.

* They are **automatically released** when garbage‑collected
* You may  **explicitly free memory** (optional):

```python
p_model.release()
```

This is recommended for long simulations or batch runs.

---

## 6. Design notes (advanced users)

* All vectors are backed by natID's fast `cnt::SafeFullVector<T>`
* No implicit memory copies between Python and C++
* `td::String` (natID) is transparently convertible to/from Python `str`
* Dynamic solvers support implicit DAE solving
* SubModels allow hierarchical initialization and reuse

---

## 7. Requirements

* Python 3.13+
* Windows: visual C++ runtimes
* NumPy (optional, for post‑processing)
* OS‑specific native libraries bundled in internally

---

## 8. License & citation

If you use **dTwin** in academic work, please cite the accompanying paper (see arXiv link).

---

## 9. Summary

`dTwin` enables **research‑grade nonlinear modeling** directly from Python while retaining ultra-fast C++ performance.

It is suitable for:

* Digital twinning
* Simulation
* Dynamic simulation
* Power systems
* Control systems
* Nonlinear estimation

Happy modeling 🚀
