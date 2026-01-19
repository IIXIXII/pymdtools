@ECHO off
REM # -----------------------------------------------------------------------------
REM # 
REM # Copyright (c) 2018 Florent TOURNOIS
REM # 
REM # Permission is hereby granted, free of charge, to any person obtaining a copy
REM # of this software and associated documentation files (the "Software"), to deal
REM # in the Software without restriction, including without limitation the rights
REM # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
REM # copies of the Software, and to permit persons to whom the Software is
REM # furnished to do so, subject to the following conditions:
REM # 
REM # The above copyright notice and this permission notice shall be included in 
REM # all copies or substantial portions of the Software.
REM # 
REM # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
REM # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
REM # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
REM # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
REM # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
REM # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
REM # SOFTWARE.
REM # 
REM # -----------------------------------------------------------------------------
@ECHO OFF
SETLOCAL EnableExtensions

REM -----------------------------------------------------------------------------
REM Entry point
REM Usage:
REM   common.bat PRINT_LINE "hello"
REM   common.bat :PRINT_LINE "hello"
REM -----------------------------------------------------------------------------

IF "%~1"=="" (
  ECHO Usage: %~nx0 ^<COMMAND^> [args...]
  ECHO Commands: PRINT_LINE CONFIGURE_DISPLAY CLEAR_SCREEN LINE_BREAK UPDATE_PIP INSTALL_REQUIREMENTS INSTALL_EDITABLE PYTHON_SETUP PYTHON_LAUNCH
  EXIT /B 2
)

SET "CMD=%~1"
IF "%CMD:~0,1%"==":" SET "CMD=%CMD:~1%"
SHIFT

CALL :%CMD% %1 %2 %3 %4 %5 %6 %7 %8 %9
EXIT /B %ERRORLEVEL%

REM -------------------------------------------------------------------------------
:PRINT_LINE
SETLOCAL EnableDelayedExpansion
SET "LINE_TO_PRINT=%~1"
ECHO(!LINE_TO_PRINT!
ENDLOCAL & EXIT /B 0

:CONFIGURE_DISPLAY
CHCP 65001 >NUL 2>&1
MODE 100,40 >NUL 2>&1
EXIT /B 0

REM -------------------------------------------------------------------------------
:CLEAR_SCREEN
CLS
CALL :PRINT_LINE "╔══════════════════════════════════════════════════════════════════════════════════════════════════╗"
CALL :PRINT_LINE "║                                                                                                  ║"
CALL :PRINT_LINE "║                                            FT                                                    ║"
CALL :PRINT_LINE "║                                                                                                  ║"
CALL :PRINT_LINE "╚══════════════════════════════════════════════════════════════════════════════════════════════════╝"
IF EXIST "%~dp0logo.bat" (
  CALL "%~dp0logo.bat" :PRINT_LOGO
)
EXIT /B 0

REM -------------------------------------------------------------------------------
:LINE_BREAK
CALL :PRINT_LINE "├──────────────────────────────────────────────────────────────────────────────────────────────────┤"
EXIT /B 0

REM -------------------------------------------------------------------------------
:UPDATE_PIP
py -V
IF ERRORLEVEL 1 (ECHO "Python launcher (py) not found." & EXIT /B 1)

py -m pip -V
IF ERRORLEVEL 1 (ECHO "pip not available." & EXIT /B 1)

py -m pip install --upgrade pip wheel setuptools
IF ERRORLEVEL 1 (ECHO "pip upgrade failed." & EXIT /B 1)

EXIT /B 0

REM -------------------------------------------------------------------------------
:INSTALL_REQUIREMENTS
SETLOCAL
SET "REQUIRE_FILE=%~1"

IF "%REQUIRE_FILE%"=="" (
  ECHO Missing requirements file.
  ENDLOCAL & EXIT /B 2
)
IF NOT EXIST "%REQUIRE_FILE%" (
  ECHO Requirements file not found: "%REQUIRE_FILE%"
  ENDLOCAL & EXIT /B 2
)

CALL :PRINT_LINE "   Install requirements %REQUIRE_FILE%"
CALL :UPDATE_PIP
IF ERRORLEVEL 1 (ENDLOCAL & EXIT /B 1)
py -m pip install -r "%REQUIRE_FILE%" || (ECHO "pip install -r failed." & ENDLOCAL & EXIT /B 1)

ENDLOCAL & EXIT /B 0

REM -------------------------------------------------------------------------------
:INSTALL_EDITABLE
CALL :PRINT_LINE "   Install editable version"
CALL :UPDATE_PIP
IF ERRORLEVEL 1 EXIT /B 1

IF NOT EXIST ".venv\Scripts\python.exe" (
  py -m venv .venv || (ECHO "venv creation failed." & EXIT /B 1)
)

.venv\Scripts\python -m pip install --upgrade pip wheel setuptools || (ECHO "venv pip upgrade failed." & EXIT /B 1)
.venv\Scripts\python -m pip install --editable . || (ECHO "editable install failed." & EXIT /B 1)
EXIT /B 0

REM -------------------------------------------------------------------------------
:PYTHON_SETUP
SETLOCAL
SET "SETUP_ACTION=%~1"
IF "%SETUP_ACTION%"=="" (
  ECHO Missing setup action.
  ENDLOCAL & EXIT /B 2
)
CALL :PRINT_LINE "   Launch python setup %SETUP_ACTION%"
py setup.py %SETUP_ACTION% || (ECHO "setup.py failed." & ENDLOCAL & EXIT /B 1)
ENDLOCAL & EXIT /B 0

REM -------------------------------------------------------------------------------
:PYTHON_LAUNCH
SETLOCAL
SET "PY_FILE=%~1"
SET "ARG1=%~2"
IF "%PY_FILE%"=="" (
  ECHO Missing python file.
  ENDLOCAL & EXIT /B 2
)
CALL :PRINT_LINE "   python %PY_FILE% %ARG1%"
py "%PY_FILE%" %ARG1% || (ECHO "python launch failed." & ENDLOCAL & EXIT /B 1)
ENDLOCAL & EXIT /B 0
REM -------------------------------------------------------------------------------
