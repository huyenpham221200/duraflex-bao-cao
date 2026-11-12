@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Cap nhat bao cao Duraflex len web ===
py -I build.py --nhap "%USERPROFILE%\Downloads"
if errorlevel 1 goto loi
git add -A
git diff --cached --quiet && (echo Khong co gi moi de day len. & goto xong)
git commit -m "Cap nhat bao cao %date% %time%"
git push
if errorlevel 1 goto loi
echo.
echo Da day len. Trang se cap nhat sau khoang 1-2 phut.
goto xong
:loi
echo.
echo CO LOI - chup man hinh nay gui Claude de xu ly.
:xong
pause
