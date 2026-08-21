"""
Convert PIVlab .txt exports into a
single gridded NetCDF file with dimensions (time, y, x).

Assumes each PIVlab txt file has columns: x, y, u, v, pass
and that x, y form the same regular grid in every file 
(standard PIVlab export behavior).
"""

import glob
import re
import numpy as np
import pandas as pd
import xarray as xr
from scipy.interpolate import griddata
import os
from pathlib import Path

def text_to_netcdf(folderPath=None, dt=1.0, save=False, outFile=None):

    if folderPath is None:
        print("A file path containting PIVLAB text files must be given as filePath=PATHTOFILES")
        return
    else:
        fileNames = os.listdir(folderPath)
        files = [folderPath +name for name in fileNames]
        storage_pre = sum(f.stat().st_size for f in Path(folderPath).rglob('*') if f.is_file()) / (1000**2) # Convert to MB
        print(f"File count: {len(files)}    |   Total Storage: {storage_pre} MB")

    # Establish the grid from the first file's unique, sorted coordinates
    first = pd.read_csv(files[0], names=["x", "y", "u", "v", "pass"])
    x_grid = np.sort(first["x"].unique())
    y_grid = np.sort(first["y"].unique())
    nx, ny = len(x_grid), len(y_grid)

    U = np.empty((len(files), ny, nx))
    V = np.empty((len(files), ny, nx))
    P = np.empty((len(files), ny, nx))

    for i, f in enumerate(files):
        u, v, p = load_frame(f, x_grid, y_grid)
        U[i], V[i], P[i] = u, v, p

    time = np.arange(len(files)) * dt

    ds = xr.Dataset(
        data_vars=dict(
            u=(["time", "y", "x"], U, {"long_name": "x-velocity", "units": "px/frame"}),
            v=(["time", "y", "x"], V, {"long_name": "y-velocity", "units": "px/frame"}),
            pass_number=(["time", "y", "x"], P, {"long_name": "PIVlab pass number"}),
        ),
        coords=dict(
            x=("x", x_grid, {"long_name": "x", "units": "px"}),
            y=("y", y_grid, {"long_name": "y", "units": "px"}),
            time=("time", time, {"long_name": "time", "units": f"{dt} s"}),
        ),
        attrs=dict(source="PIVlab txt export", created_by="pivlab_to_netcdf.py"),
    )

    storage_post = ds.nbytes / (1000**2) # Convert to MB
    print(f"Created xarray dataset. Total storage: {storage_post} MB.   |   Reduction in storage : {storage_post/storage_pre}")

    if save:
        ds.to_netcdf(outFile)
        print(f"Wrote {outFile}  (dims: time={len(files)}, y={ny}, x={nx})")

    return ds


def natural_sort_key(s):
    # Sort files in order
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def load_frame(path, x_grid, y_grid):

    # Load the first file to create the shared grid
    df = pd.read_csv(path, names=["x", "y", "u", "v", "pass"])

    nx, ny = len(x_grid), len(y_grid)

    # Data already lies exactly on (x_grid, y_grid) -> just reshape.
    # Sort explicitly by x and y
    df_sorted = df.sort_values(by=["y", "x"], kind="mergesort")

    same_grid = (
        len(df_sorted) == nx * ny
        and np.allclose(np.sort(df["x"].unique()), x_grid)
        and np.allclose(np.sort(df["y"].unique()), y_grid)
    )

    if same_grid:
        u = df_sorted["u"].to_numpy().reshape(ny, nx)
        v = df_sorted["v"].to_numpy().reshape(ny, nx)
        p = df_sorted["pass"].to_numpy().reshape(ny, nx)
    else:
        # Fallback: irregular / masked points -> interpolate onto the grid
        X, Y = np.meshgrid(x_grid, y_grid)  # shape (ny, nx)
        pts = np.column_stack([df["x"].to_numpy(), df["y"].to_numpy()])
        u = griddata(pts, df["u"].to_numpy(), (X, Y), method="linear")
        v = griddata(pts, df["v"].to_numpy(), (X, Y), method="linear")
        p = griddata(pts, df["pass"].to_numpy(), (X, Y), method="nearest")

    return u, v, p
