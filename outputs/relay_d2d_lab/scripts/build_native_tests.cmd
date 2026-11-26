@echo off
setlocal
if not defined VS_BUILD_ROOT set "VS_BUILD_ROOT=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
call "%VS_BUILD_ROOT%\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
if not exist "%~dp0..\.build\native_tests" mkdir "%~dp0..\.build\native_tests"
pushd "%~dp0..\.build\native_tests"
cl.exe /nologo /EHsc /std:c++17 /W4 "%~dp0..\tests\native_protocol.cpp" /Fe:native_protocol.exe
set "BUILD_RESULT=%ERRORLEVEL%"
popd
exit /b %BUILD_RESULT%
