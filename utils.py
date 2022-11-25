"""
Utilities
"""

__all__ = ["exec_char_stream", "Platform"]

from selenium.webdriver.remote.webdriver import WebDriver as wd
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait as wdw
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains as AC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException, MoveTargetOutOfBoundsException
from selenium.webdriver.chrome.options import Options

import json
import selenium
import os
import time

def exec_char_stream(prompt, log, stream, terminal_phrase):
    terminal_phrase_encoded = []
    for term in terminal_phrase:
        if isinstance(term, str):
            terminal_phrase_encoded.append(term.encode())
        else:
            terminal_phrase_encoded.append(term)
    # print("phr", terminal_phrase_encoded)
    execption = None
    try:
        cmd_out = b""
        line_buffer = b""
        for out_c in stream:
            # print(out_c, end="|")
            if isinstance(out_c, int):
                out_c = bytes([out_c])
            if isinstance(out_c, str):
                out_c = out_c.encode()
            cmd_out += out_c
            line_buffer += out_c
            if out_c == '\n'.encode():
                print(prompt, ":", line_buffer)
                line_buffer = b""
            for term in terminal_phrase_encoded:
                # print("check", term, cmd_out, "end check")
                if term in cmd_out:
                    if len(line_buffer):
                        print(prompt, ":", line_buffer)
                    break
            else:
                continue
            break
    except Exception as e:
        print(e)
        execption = e
    finally:
        with open(log, "wb") as f:
            f.write(cmd_out)
            if execption is not None:
                f.write(str(execption).encode())
    return cmd_out

class Platform:
    def __init__(self, commit) -> None:
        print("! initializing online platform")
        with open("config.json", "r") as f:
            cfg = json.load(f)

        chrome_options = Options()
        chrome_options.add_argument("--headless")

        print("! launching Chrome")
        d = selenium.webdriver.Chrome(
            service=ChromeService(
                ChromeDriverManager().install()
            ),
            options=chrome_options
        )

        # lab cs
        print("@ lab.cs")
        d.get("https://lab.cs.tsinghua.edu.cn/thinpad/")
        lab_cs_login = d.find_element(By.XPATH, "//div[@class='form-signin']/a")
        wdw(d, 5).until(EC.element_to_be_clickable(lab_cs_login))
        lab_cs_login.click()

        # yx portal
        print("@ yx protal")
        yx_login = By.CLASS_NAME, "primary"
        wdw(d, 5).until(EC.element_to_be_clickable(yx_login)).click()

        
        def auth():
            # git tsinghua
            print("@ git tsinghua")
            git_tsinghua_login = By.TAG_NAME, 'button'
            wdw(d, 5).until(EC.element_to_be_clickable(git_tsinghua_login)).click()
            time.sleep(1)

            # tsinghua auth
            print("@ tsinghua auth")
            thu_login = By.XPATH, '//form/div/a[@onclick]'
            wdw(d, 5).until(EC.element_to_be_clickable(thu_login))
            d.find_element(By.ID, 'i_user').send_keys(cfg["user_id"])
            d.find_element(By.ID, 'i_pass').send_keys(cfg["user_password"])
            d.find_element(*thu_login).click()
            time.sleep(3)

        while True:
            auth()
            # CSRF detected, retry
            if len(d.find_elements(By.TAG_NAME, 'svg')) == 0:
                break
            print("! csrf detected, retry")
            

        # redirect to build selection
        while True:
            try:
                print("@ fetching CI")
                CI_list = By.XPATH, "//form//button[@class='btn btn-primary']"
                wdw(d, 5).until(EC.element_to_be_clickable(CI_list))
                time.sleep(1)
                d.find_element(*CI_list).click()
            except TimeoutException:
                continue
            else:
                break

        while True:
            for tr in d.find_elements(By.TAG_NAME, 'h4'):
                if "CI" in tr.text:
                    break
            else:
                time.sleep(0.5)
                print("Waiting for CI ...")
                continue
            break

        for tr in d.find_elements(By.TAG_NAME, 'tr'):
            if commit in tr.text:
                tr.click()
                print("CI found")

        # memory selection
        mem_sel = By.XPATH, "//div[@class='input-group']/select"
        wdw(d, 10).until(EC.presence_of_element_located(mem_sel))
        mem = Select(d.find_element(*mem_sel))

        self.d, self.cfg, self.mem = d, cfg, mem

    def hold_reset(self):
        print("rst hold")
        try:
            AC(self.d).click_and_hold(self.d.find_element(By.NAME, "clk")).move_by_offset(0, -50).release().perform()
        except MoveTargetOutOfBoundsException:
            pass  # still works

    def click_reset(self):
        print("rst click")
        self.d.find_element(By.NAME, "clk").click()
        
    def upload_rbl(self):
        print("loading RBL")
        self.upload_file('base', os.path.join(self.cfg['ucore_root'], "bin/rbl.img"))
        
    def upload_ucore(self):
        print("loading uCore")
        self.upload_file('ext', os.path.join(self.cfg['ucore_root'], "bin/ucore.img"))  
        
    def upload_file(self, name, path):
        print("updating %s with %s" % (name, path))
        self.mem.select_by_value(name)
        file_upload = By.XPATH, "//input[@type='file']"
        self.d.find_elements(*file_upload)[-1].send_keys(path)
        self.d.find_elements(By.XPATH, "//button[@type='submit']")[-1].click()
        time.sleep(0.5)
        wdw(self.d, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "text-success")))

    def get_serial(self):
        try:
            br = Select(self.d.find_element(By.ID, "ttl-baudrate"))
            br.select_by_visible_text("115200")
            for button in self.d.find_elements(By.TAG_NAME, 'input'):
                if button.get_attribute('value') == '打开串口':
                    button.click()
                    print("opening serial")
                    break
        except ElementNotInteractableException:
            pass
        return wdw(self.d, 1).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'code')))[0].text