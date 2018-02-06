import logging
import re
import pexpect
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Engine(object):

    """Docstring for ChildPlus. """

    def __init__(self, name):
        """TODO: Docstring for __init__.
        :returns: TODO

        """
        self.child = None
        self.cnt_method = ''
        self.cnt_info = ''
        self.cnt_status = False
        self.cnt_username = ''
        self.logger = logging.getLogger(name)

    def telnet(
            self,
            username,
            password,
            ip,
            port=23,
            prompt_username='sername|ogin:',
            prompt_password='assword:',
            prompt_refuse='refused',
            prompt_stop='[$>#]',
            timeout_connect=10,
            timeout_echo=2):
        """telnet
        :prompt_refuse: refuse prompt, e.g 'refused'
        :prompt_stop: stop prompt, e.g '[cyber@centos]$'
        :timeout_connect: connect timeout
        :timeout_echo: echo timeout
        :returns: cnt_status, True/False

        """
        child = pexpect.spawn(
            'telnet %s %s' %
            (ip, port), timeout=timeout_connect)
        index = child.expect(
            [prompt_username, prompt_refuse, pexpect.TIMEOUT, pexpect.EOF])
        if index == 0:
            child.sendline(username)
            index_pw = child.expect(
                [prompt_password, pexpect.TIMEOUT],
                timeout=timeout_echo)
            if index_pw == 0:
                child.sendline(password)
                index_tmp = child.expect(
                    [prompt_username, prompt_stop, pexpect.TIMEOUT, pexpect.EOF],
                    timeout=timeout_echo)
                if index_tmp == 0:
                    cnt_method = 'telnet'
                    cnt_info = 'wrone_password'
                    cnt_status = False
                    cnt_username = ''
                elif index_tmp == 1:
                    cnt_method = 'telnet'
                    cnt_info = 'success'
                    cnt_status = True
                    cnt_username = username
                else:
                    cnt_method = 'telnet'
                    cnt_info = 'timeout_echo'
                    cnt_status = False
                    cnt_username = ''
            else:
                cnt_method = 'telnet'
                cnt_info = 'timeout_echo'
                cnt_status = False
                cnt_username = ''
        elif index == 1:
            cnt_method = 'telnet'
            cnt_info = 'service_refuse'
            cnt_status = False
            cnt_username = ''
        elif index == 2:
            cnt_method = 'telnet'
            cnt_info = 'timeout_connect'
            cnt_status = False
            cnt_username = ''
        else:
            cnt_method = 'telnet'
            cnt_info = 'timeout_echo'
            cnt_status = False
            cnt_username = ''
        self.child = child
        self.cnt_method = cnt_method
        self.cnt_info = cnt_info
        self.cnt_status = cnt_status
        self.cnt_username = cnt_username
        if cnt_status:
            self.logger.info('The connection is successful')
        else:
            self.logger.info('The connection fails')
        return cnt_status

    def ssh(
            self,
            username,
            password,
            ip,
            port=22,
            version=2,
            prompt_password='assword:',
            prompt_refuse='refused',
            prompt_stop='[$>#]',
            timeout_connect=10,
            timeout_echo=2):
        """ssh
        :prompt_refuse: refuse prompt, e.g 'refused'
        :prompt_stop: stop prompt, e.g '[cyber@centos]$'
        :timeout_connect: connect timeout
        :timeout_echo: echo timeout
        :returns: cnt_status, True/False

        """
        child = pexpect.spawn('ssh -%s %s@%s -p %s' %
                              (version, username, ip, port),
                              timeout=timeout_connect)
        index_ssh = child.expect(
            ['yes', prompt_password, prompt_refuse, pexpect.TIMEOUT, pexpect.EOF])
        if index_ssh == 0:
            child.sendline('yes')
            index_ssh_pw = child.expect(
                [prompt_password, pexpect.TIMEOUT, pexpect.EOF],
                timeout=timeout_echo)
            if index_ssh_pw == 0:
                child.sendline(password)
            else:
                cnt_method = 'ssh' + str(version)
                cnt_info = 'timeout_echo'
                cnt_status = False
                cnt_username = ''
        elif index_ssh == 1:
            child.sendline(password)
        elif index_ssh == 2:
            cnt_method = 'ssh' + str(version)
            cnt_info = 'service_refuse'
            cnt_status = False
            cnt_username = ''
        elif index_ssh == 3:
            cnt_method = 'ssh' + str(version)
            cnt_info = 'timeout_connect'
            cnt_status = False
            cnt_username = ''
        index_tmp = child.expect(
            [prompt_password, prompt_stop, pexpect.TIMEOUT, pexpect.EOF],
            timeout=timeout_echo)
        if index_tmp == 0:
            cnt_method = 'ssh' + str(version)
            cnt_info = 'wrong_password'
            cnt_status = False
            cnt_username = ''
        elif index_tmp == 1:
            cnt_method = 'ssh' + str(version)
            cnt_info = 'success'
            cnt_status = True
            cnt_username = username
        else:
            cnt_method = 'ssh' + str(version)
            cnt_info = 'timeout_echo'
            cnt_status = False
            cnt_username = username
        self.child = child
        self.cnt_method = cnt_method
        self.cnt_info = cnt_info
        self.cnt_status = cnt_status
        self.cnt_username = cnt_username
        if cnt_status:
            self.logger.info('The connection is successful')
        else:
            self.logger.info('The connection fails')

    def get_prompt_stop(self, prompt_stop='[$>#]', timeout_echo=0.5):
        """get the host's stop prompt"""
        #  The password needs to be changed. Change now? [Y/N]:
        index = self.child.expect(
            ['now?', pexpect.EOF, pexpect.TIMEOUT],
            timeout_echo)
        if index == 0:
            self.child.sendline('n')
        self.child.sendline()
        index_get = self.child.expect(
            [prompt_stop, pexpect.TIMEOUT, pexpect.EOF],
            timeout_echo)
        if index_get == 0:
            prompt_stop = (
                self.child.before + self.child.after).split(b'\r\n')[-1][1:-1]
            return prompt_stop
        else:
            self.logger.info('Get prompt_stop fails')
            return b''

    def cmd_show(
            self,
            str_command,
            prompt_more,
            prompt_stop,
            prompt_confirm=' ',
            timeout_echo=2):
        """command show result

        :str_command: show command
        :prompt_more: more prompt, e.g '--More--'/'--more--'
        :prompt_stop: stop prompt, e.g '[cyber@centos]$'
        :prompt_confirm: confirm prompt, command sent when an more prompt appear, e.g ' '
        :timeout_echo: echo timeout, e.g 2
        :returns: result, e.g 'xxx'/''

        """
        show_result = b''
        #  清空上一个指令的残留buffer，判断标准是直到buffer中不存在prompt_stop为止
        index1 = self.child.expect(
            [prompt_stop, pexpect.TIMEOUT, pexpect.EOF], 0.1)
        if index1 == 0:
            while True:
                index_3 = self.child.expect(
                    [prompt_stop, pexpect.TIMEOUT, pexpect.EOF], 0.1)
                if index_3 == 0:
                    continue
                else:
                    break
        else:
            pass
        self.child.sendline(str_command)
        while True:
            index2 = self.child.expect(
                [prompt_more, prompt_stop, pexpect.EOF, pexpect.TIMEOUT],
                timeout_echo)
            if index2 == 0:
                show_result += self.child.before + self.child.after
                self.child.sendline(prompt_confirm)
            elif index2 == 1:
                break
            elif index2 == 2:
                show_result += b'\r\ntimeout\r\n'
                break
            elif index2 == 3:
                show_result += b'\r\nEOF\r\n'
                break
        return show_result

    def cmd_config(
            self,
            str_commands,
            prompt_more,
            prompt_stop,
            prompt_confirm=' ',
            prompt_error='',
            timeout_echo=2):
        """command config

        :str_commands: config commands
        :prompt_more: more prompt, e.g '--More--'/'--more--'
        :prompt_stop: stop prompt, e.g '[cyber@centos]$'
        :prompt_confirm: confirm prompt, command sent when an more prompt appear, e.g ' '
        :prompt_error: error prompt, if prompt_error == '', process will ignore the error, otherwise it will stop and print the error.
        :timeout_echo: echo timeout, e.g 2
        :returns: config status, True/False

        """
        commands = [command.strip()
                    for command in re.split(r'[\r\n]{1,}', str_commands)
                    if command.strip() and not command.strip().startswith('#')]
        for command in commands:
            cfg_result = self.cmd_show(
                command,
                prompt_more,
                prompt_stop,
                prompt_confirm,
                timeout_echo)
            if prompt_error and re.search(
                    prompt_error.encode(), cfg_result, re.I):
                self.logger.warn(f"Config error on {cfg_result}")
                return False
        else:
            return True

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.child.close()


def init_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S',)


def main():
    init_logger()
    username = 'cyber'
    password = 'gddx@6F'
    ip = '10.104.123.189'
    port = 64922

    with Engine('gdgyy') as engine:
        engine.ssh(username, password, ip, port)
        prompt_stop = engine.get_prompt_stop()
        foo = engine.cmd_show('more index.html', '--More--', prompt_stop)
        print(foo)
        bar = engine.cmd_show('ls', '--More--', prompt_stop)
        print(bar)
        foobar = engine.cmd_config('touch gdgyy', '--More--', prompt_stop)


if __name__ == "__main__":
    main()
