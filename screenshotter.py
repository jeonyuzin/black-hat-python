import win32gui
import win32ui
import win32con
import win32api

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

# 이미지 내용 생성을 다루는 객체
mem_dc = img_dc.CreateCompatibleDC()

# 비트맵 형식으로 변환해서 기록
screenshot = win32ui.CreateBitmap() #이미지 객체를 생성하고
screenshot.CreateCompatibleBitmap(img_dc, width, height)# 비트맵 호환 변환
mem_dc.SelectObject(screenshot) #이미지 할당

# 할당한 이미지 데이터를 비트 단위로 복사해서 메모리 영역에 저장
mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)

# save the bitmap to a file
screenshot.SaveBitmapFile(mem_dc, 'c:\\WINDOWS\\Temp\\screenshot.bmp')

# free our objects 
mem_dc.DeleteDC()
win32gui.DeleteObject(screenshot.GetHandle())
