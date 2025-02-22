from functools import partial
from io import BytesIO
from logger_tt import logger
import os
from pathlib import Path
import platform
import requests
import sys
import tarfile
from tempfile import gettempdir
from zipfile import ZipFile

import shutil

from model.dialogue import (
    show_dialogue_conditional,
    show_fatal_error,
    show_information,
    show_warning,
)
from window.runner_panel import RunnerPanel


class SteamcmdInterface:
    """
    Create SteamcmdInterface object to provide an interface for steamcmd functionality
    """

    def __init__(self, steamcmd_prefix: str, validate: bool) -> None:
        logger.debug("Initializing SteamcmdInterface")
        self.steamcmd_install_path = str(Path(steamcmd_prefix, "steamcmd").resolve())
        self.steamcmd_steam_path = str(Path(steamcmd_prefix, "steam").resolve())
        self.system = platform.system()
        self.validate_downloads = validate

        if self.system == "Darwin":
            self.steamcmd_url = (
                "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_osx.tar.gz"
            )
            self.steamcmd = str(
                Path(os.path.join(self.steamcmd_install_path, "steamcmd.sh")).resolve()
            )
        elif self.system == "Linux":
            self.steamcmd_url = (
                "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz"
            )
            self.steamcmd = str(
                Path(os.path.join(self.steamcmd_install_path, "steamcmd.sh")).resolve()
            )
        elif self.system == "Windows":
            self.steamcmd_url = (
                "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
            )
            self.steamcmd = str(
                Path(os.path.join(self.steamcmd_install_path, "steamcmd.exe")).resolve()
            )
        else:
            show_fatal_error(
                "SteamcmdInterface",
                f"Found platform {self.system}. steamcmd is not supported on this platform.",
            )
            return

        if not os.path.exists(self.steamcmd_install_path):
            os.makedirs(self.steamcmd_install_path)
            logger.debug(
                f"SteamCMD does not exist. Creating path for installation: {self.steamcmd_install_path}"
            )

        if not os.path.exists(self.steamcmd_steam_path):
            os.makedirs(self.steamcmd_steam_path)
        self.steamcmd_appworkshop_acf_path = str(
            Path(
                os.path.join(
                    self.steamcmd_steam_path,
                    "steamapps",
                    "workshop",
                    "appworkshop_294100.acf",
                )
            ).resolve()
        )
        self.steamcmd_content_path = str(
            Path(
                os.path.join(
                    self.steamcmd_steam_path, "steamapps", "workshop", "content"
                )
            ).resolve()
        )
        logger.debug("Finished SteamcmdInterface initialization")

    def download_mods(self, publishedfileids: list, runner: RunnerPanel):
        """
        This function downloads a list of mods from a list publishedfileids

        https://developer.valvesoftware.com/wiki/SteamCMD

        :param appid: a Steam AppID to pass to steamcmd
        :param publishedfileids: list of publishedfileids
        :param runner: a RimSort RunnerPanel to interact with
        """
        runner.message("Checking for steamcmd...")
        if self.steamcmd is not None and os.path.exists(self.steamcmd):
            runner.message(
                f"Got it: {self.steamcmd}\n"
                + f"Downloading list of {str(len(publishedfileids))} "
                + f"publishedfileids to: {self.steamcmd_steam_path}"
            )
            script = [
                f"force_install_dir {self.steamcmd_steam_path}",
                "login anonymous",
            ]
            download_cmd = "workshop_download_item 294100"
            for publishedfileid in publishedfileids:
                if self.validate_downloads:
                    script.append(f"{download_cmd} {publishedfileid} validate")
                else:
                    script.append(f"{download_cmd} {publishedfileid}")
            script.extend(["quit\n"])
            script_path = str(
                Path(os.path.join(gettempdir(), "steamcmd_script.txt")).resolve()
            )
            with open(script_path, "w") as script_output:
                script_output.write("\n".join(script))
            runner.message(f"Compiled & using script: {script_path}")
            runner.execute(
                self.steamcmd,
                [f"+runscript {script_path}"],
                len(publishedfileids),
            )
        else:
            runner.message("SteamCMD was not found. Please setup SteamCMD first!")

    def setup_steamcmd(
        self, symlink_source_path: str, reinstall: bool, runner: RunnerPanel
    ) -> None:
        installed = None
        if reinstall:
            runner.message("Existing steamcmd installation found!")
            runner.message(
                f"Deleting existing installation from: {self.steamcmd_install_path}"
            )
            shutil.rmtree(self.steamcmd_install_path)
            os.makedirs(self.steamcmd_install_path)
            # shutil.rmtree(self.steamcmd_steam_path)
            # os.makedirs(self.steamcmd_steam_path)
        if not os.path.exists(self.steamcmd):
            try:
                runner.message(
                    f"Downloading & extracting steamcmd release from: {self.steamcmd_url}"
                )
                if ".zip" in self.steamcmd_url:
                    with ZipFile(
                        BytesIO(requests.get(self.steamcmd_url).content)
                    ) as zipobj:
                        zipobj.extractall(self.steamcmd_install_path)
                    runner.message(f"Installation completed")
                    installed = True
                elif ".tar.gz" in self.steamcmd_url:
                    with requests.get(
                        self.steamcmd_url, stream=True
                    ) as rx, tarfile.open(fileobj=rx.raw, mode="r:gz") as tarobj:
                        tarobj.extractall(self.steamcmd_install_path)
                    runner.message(f"Installation completed")
                    installed = True
            except:
                runner.message("Installation failed")
                show_fatal_error(
                    "SteamcmdInterface",
                    f"Failed to download steamcmd for {self.system}",
                    f"Did the file/url change?\nDoes your environment have access to the internet?",
                )
        else:
            runner.message("SteamCMD already installed...")
            show_warning(
                "SteamcmdInterface",
                f"A steamcmd runner already exists at: {self.steamcmd}",
            )
            answer = show_dialogue_conditional(
                "Reinstall?",
                "Would you like to reinstall SteamCMD?",
                f"Existing install: {self.steamcmd_install_path}",
            )
            if answer == "&Yes":
                runner.message(f"Reinstalling SteamCMD: {self.steamcmd_install_path}")
                self.setup_steamcmd(symlink_source_path, True, runner)
        if installed:
            if not os.path.exists(self.steamcmd_content_path):
                os.makedirs(self.steamcmd_content_path)
                runner.message(
                    f"Workshop content path does not exist. Creating for symlinking:\n\n{self.steamcmd_content_path}\n"
                )
            symlink_destination_path = str(
                Path(os.path.join(self.steamcmd_content_path, "294100"))
            )
            runner.message(f"Symlink source : {symlink_source_path}")
            runner.message(f"Symlink destination: {symlink_destination_path}")
            if os.path.exists(symlink_destination_path):
                runner.message(
                    f"Symlink destination already exists! Please remove existing destination:\n\n{symlink_destination_path}\n"
                )
            else:
                answer = show_dialogue_conditional(
                    "Create symlink?",
                    "Would you like to create a symlink as followed?",
                    f"[{symlink_source_path}] -> " + symlink_destination_path,
                )
                if answer == "&Yes":
                    runner.message(
                        f"[{symlink_source_path}] -> " + symlink_destination_path
                    )
                    if self.system != "Windows":
                        os.symlink(
                            symlink_source_path,
                            symlink_destination_path,
                            target_is_directory=True,
                        )
                    else:
                        from _winapi import CreateJunction

                        CreateJunction(symlink_source_path, symlink_destination_path)


if __name__ == "__main__":
    sys.exit()
