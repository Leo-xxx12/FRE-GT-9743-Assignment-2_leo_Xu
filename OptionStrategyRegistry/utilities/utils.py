import os, sys
import pandas as pd
import platform
from io import StringIO, BytesIO
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import torch
import pickle


def initialise():
    sys.path.append(os.path.dirname(os.getcwd()))


def get_config_folder():
    tmp_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(tmp_path, "configs")


def get_device():
    if platform.system().upper() == "DARWIN":
        return torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    elif platform.system().upper() == "WINDOWS":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")


### G - drive
def get_google_driver_handler():
    gauth = GoogleAuth()
    gauth.settings["client_config_file"] = os.path.join(
        get_config_folder(), "client_secrets.json"
    )
    gauth.LoadCredentialsFile(os.path.join(get_config_folder(), "credentials.json"))
    return GoogleDrive(gauth)


def query_g_drive(file_name: str, handler: GoogleDrive):
    file_list = handler.ListFile().GetList()
    for file in file_list:
        if file["title"] == file_name:
            return file["id"]
    raise Exception(f"Cannot find file {file_name}.")


def read_parquet_from_g_drive(file_name: str, handler: GoogleDrive):
    file_id = query_g_drive(file_name=file_name, handler=handler)
    file = handler.CreateFile({"id": file_id})
    file.GetContentFile(file_name)
    df = pd.read_parquet(file_name)
    os.remove(file_name)
    return df


def read_csv_from_g_drive(file_name: str, handler: GoogleDrive):
    handler = get_google_driver_handler()
    file_id = query_g_drive(file_name=file_name, handler=handler)
    file = handler.CreateFile({"id": file_id})
    return pd.read_csv(StringIO(file.GetContentString()))


def read_xlsx_from_g_drive(file_name, handler):
    file_id = query_g_drive(file_name=file_name, handler=handler)
    file = handler.CreateFile({"id": file_id})
    file.FetchContent()

    content = file.content.getvalue()
    return pd.read_excel(BytesIO(content))


def read_pkl_from_g_drive(file_name: str, handler: GoogleDrive):
    file_id = query_g_drive(file_name=file_name, handler=handler)
    file = handler.CreateFile({"id": file_id})
    temp_path = f"/tmp/{file_name}"
    file.GetContentFile(temp_path)
    with open(temp_path, "rb") as f:
        obj = pickle.load(f)
    os.remove(temp_path)
    return obj


def send_file_to_google_drive(input_df: pd.DataFrame, folder_name: str, file_name: str):
    file_format = file_name.split(".")[1]
    if file_format == "parquet":
        input_df.to_parquet(file_name)
    elif file_format == "pkl" or file_format == "pickle":
        with open(file_name, "wb") as f:
            pickle.dump(input_df, f)
    else:
        input_df.to_csv(file_name)

    g_handler = get_google_driver_handler()
    file_list = g_handler.ListFile().GetList()

    this_folder = None
    for file in file_list:
        if file["title"] == folder_name:
            this_folder = file["id"]
            break
    assert this_folder is not None, f"Cannot find folder {folder_name} in Google Drive."
    file_drive = g_handler.CreateFile(
        {"title": file_name, "parents": [{"id": this_folder}]}
    )
    file_drive.SetContentFile(file_name)
    file_drive.Upload()

    os.remove(file_name)
    print(f"Upload {file_name} to Google Drive folder {folder_name} successfully.")


###
