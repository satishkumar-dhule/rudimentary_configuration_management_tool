import yaml
from yaml import loader
import grp
import pwd
import os
import subprocess
from subprocess import STDOUT, check_call


class CoolFile:
    """File manupulation class"""

    def __init__(self) -> None:
        pass

    def __init__(self, file_prop) -> None:
        self.action = file_prop.get('action')
        self.fname = file_prop.get('name')
        self.permission = file_prop.get('permission', None)
        self.group = file_prop.get('group', None)
        self.owner = file_prop.get('owner', None)
        self.content = file_prop.get('content', None)
        self.execute_action = False
        self.change_permission = False
        self.change_group = False
        self.change_user = False
        self.change_content = False
        self.change_required = False
        if not os.path.exists(self.fname) and self.action == "create":
            self.execute_action = True
            if self.permission:
                self.change_permission = True
            if self.group:
                self.change_group = True
            if self.owner:
                self.change_user = True
            if self.content:
                self.change_content = True
        elif os.path.exists(self.fname) and self.action == "create":
            self.execute_action = False
            stat_info = os.stat(self.fname)
            uid = stat_info.st_uid
            gid = stat_info.st_gid
            f_user = pwd.getpwuid(uid)[0]
            f_group = grp.getgrgid(gid)[0]
            if self.permission and oct(stat_info.st_mode)[-3:] != oct(self.permission)[2:]:
                self.change_permission = True
            if self.owner and f_user != self.owner:
                self.change_user = True
            if self.group and f_group != self.group:
                self.change_group = True
            with open(self.fname, "r") as fp:
                f_content = fp.read()
            if self.content and f_content != self.content:
                self.change_content = True
        elif self.action == "delete":
            if not os.path.exists(self.fname):
                self.execute_action = False
            else:
                self.execute_action = True
            self.change_permission = False
            self.change_group = False
            self.change_user = False
            self.change_content = False

    def __str__(self) -> str:
        out = ""
        for property, value in vars(self).items():
            out += f"{property} : {value}\n"
        return out

    def __repr__(self) -> str:
        out = ""
        for property, value in vars(self).items():
            out += f"{property} : {value}\n"
        return out

    def apply(self):
        # print(self.fname,self.action,self.execute_action)
        if self.action == 'delete' and self.execute_action:
            print(f"{self.action}ing {self.fname} ... : ", end="")
            os.remove(self.fname)
            print(f"SUCCESS")
            return
        elif self.action == 'create' and (self.execute_action or self.change_content):
            with open(self.fname, "w") as fp:
                print(f"{self.action}ing {self.fname} and/or adding content... : ", end="")
                if self.content:
                    fp.writelines(self.content)
                print(f"SUCCESS")
        if self.permission and self.change_permission:
            print(f"Changing permission for {self.fname} ... : ", end="")
            os.chmod(self.fname, self.permission)
            print(f"SUCCESS")
        if self.owner and self.group and self.change_user or self.change_group:
            print(f"Changing group/owner for {self.fname} ... : ", end="")
            uid = grp.getgrnam(self.owner).gr_gid
            gid = grp.getgrnam(self.group).gr_gid

            os.chown(self.fname, uid, gid)
            print(f"SUCCESS")

    def plan(self):
        self.change_required = False
        print(f"Plan for file {self.action}:{self.fname} -->")
        if self.action == "create":
            if self.execute_action:
                print(f"- Apply {self.action} {self.fname}")
                self.change_required = True
            if self.change_content:
                print(f"- Apply change content")
                self.change_required = True
            if self.change_permission:
                print(f"- Apply change permissions: {oct(self.permission)}")
                self.change_required = True
            if self.change_group:
                print(f"- Apply change group: {self.group}")
                self.change_required = True
            if self.change_user:
                print(f"- Apply change owner: {self.owner}")
                self.change_required = True
        elif self.execute_action and self.action == "delete":
            print(f"- Apply {self.action} {self.fname}")
            self.change_required = True
        if not self.change_required:
            print(f"- No changes required for {self.fname}")
        print()


class LoaderClass:
    def load_input(self, input_file="testy.yml"):
        data = dict()
        with open(file=input_file, mode="r") as fd:
            try:
                data = yaml.safe_load(fd)
            except yaml.YAMLError as exc:
                print(exc)
        return data


class CoolPkg:
    """Class for managing the packages"""

    def __init__(self) -> None:
        pass

    def __init__(self, pkg_record: dict) -> None:
        self.name = pkg_record.get('name')
        self.action = pkg_record.get('action')
        self.command = pkg_record.get('command')
        if self.is_pkg_valid():
            self.is_installed = self.is_pkg_installed()
            self.valid = True
        else:
            self.is_installed = False
            self.valid = False

    def apply(self):
        a = -1
        if not self.is_pkg_valid():
            print(f"{self.name} is invalid")
        elif self.action in ["install", "add"] and not self.is_installed:
            print(f"Installing {self.name} ... : ")
            if not self.is_pkg_installed():
                a = check_call(['apt-get', 'install', '-y', self.name],
                               stdout=open(os.devnull, 'wb'), stderr=STDOUT)
                if self.command and a==0:
                    for c in self.command.split(';'):
                        print(f"Executing {c.split(' ')}")
                        a = check_call(c.split(' '),
                                       stdout=open(os.devnull, 'wb'), stderr=STDOUT)

            if a == 0:
                print("SUCCESS")
            else:
                print("FAILED")
        elif self.action in ["uninstall", "remove"] and self.is_installed:
            if self.is_pkg_installed():
                print(f"{self.action}ing {self.name}... : ", end="")
                a = check_call(['apt-get', 'purge', '-y', self.name],
                               stdout=open(os.devnull, 'wb'), stderr=STDOUT)

            if a == 0:
                print("SUCCESS")
            else:
                print("FAILED")
        else:
            return
        print()

    def is_pkg_installed(self):
        devnull = open(os.devnull, "w")
        try:
            retval = subprocess.call(
                ["dpkg", "-s", self.name], stdout=devnull, stderr=subprocess.STDOUT)
            # print(f"ret value for {self.name} {retval}")
        except Exception as e:
            print(e)
        devnull.close()
        if retval != 0:
            return False
        return True

    def is_pkg_valid(self):
        devnull = open(os.devnull, "w")
        try:
            retval = subprocess.call(
                ["apt", "show", self.name], stdout=devnull, stderr=subprocess.STDOUT)
        except Exception as e:
            print(e)
        devnull.close()
        if retval != 0:
            return False
        return True

    def plan(self):
        self.change_required = False
        # print(self.is_installed , self.action)
        print(f"Plan for pkg {self.action}:{self.name} -->")
        if not self.valid:
            print(f"- Not valid pkg {self.name}")
            return
        elif self.action in ["install", "add"] and not self.is_installed:
            print(f"- Apply {self.action} {self.name}")
            if self.command:
                print(f"- Apply command {self.command}")
            self.change_required = True
        elif self.action in ["uninstall", "remove"] and self.is_installed:
            print(f"- Apply {self.action} {self.name}")
            self.change_required = True
        else:
            print(f"- No action required ")
        print()


if __name__ == "__main__":
    data = LoaderClass().load_input()
    change_required = False
    for pkg in data['packages']:
        package_record = CoolPkg(pkg)
        package_record.plan()
        if package_record.change_required:
            change_required = True

    for f in data['files']:
        file_record = CoolFile(f)
        file_record.plan()
        if file_record.change_required:
            change_required = True

    if change_required:
        print(f"Do you want to execute this plan: [Yes|No]\n")
        user_response = input()
        if user_response == "Yes":
            try:
                for pkg in data['packages']:
                    package_record = CoolPkg(pkg)
                    package_record.apply()
                for f in data['files']:
                    file_record = CoolFile(f)
                    file_record.apply()
            except Exception as e:
                print(f"Exception occured for {f.fname}: {e}")

        else:
            print("Aborting")
