@ECHO off
REM ===========================================================================
REM                   Author: Florent TOURNOIS | License: MIT                  
REM ===========================================================================

SETLOCAL EnableExtensions

REM -----------------------------------------------------------------------------
REM Init
REM -----------------------------------------------------------------------------
SET "MYPATH=%~dp0"

CD /D "%MYPATH%" || (ECHO ERROR: cannot cd to "%MYPATH%" & EXIT /B 1)

SET "MODULE=pymdtools"
SET "FUN=%MYPATH%scripts\common.bat"
SET "ARGUMENT=%~1"

IF "%ARGUMENT%"=="" (
  ECHO Usage: %~nx0 ^<requirements^|install_editable^|<setup_action>^>
  EXIT /B 2
)

IF NOT EXIST "%FUN%" (
  ECHO ERROR: common script not found: "%FUN%"
  EXIT /B 1
)

REM -----------------------------------------------------------------------------
REM Version
REM -----------------------------------------------------------------------------
IF EXIST "%MYPATH%%MODULE%\version.bat" (
  CALL "%MYPATH%%MODULE%\version.bat"
) ELSE (
  SET "VERSION=Not found"
)

REM -----------------------------------------------------------------------------
REM Main loop
REM -----------------------------------------------------------------------------
:STARTAGAIN
CALL "%FUN%" :CONFIGURE_DISPLAY
CALL "%FUN%" :CLEAR_SCREEN
CALL "%FUN%" :PRINT_LINE "    VERSION=%VERSION%"
CALL "%FUN%" :PRINT_LINE "    MYPATH=%MYPATH%"
CALL "%FUN%" :LINE_BREAK

TITLE "[%MODULE%] MAKE %ARGUMENT%"

IF /I "%ARGUMENT%"=="requirements" (
  CALL "%FUN%" :INSTALL_REQUIREMENTS "requirements.txt"
  IF ERRORLEVEL 1 GOTO :FAILED
) ELSE IF /I "%ARGUMENT%"=="install_editable" (
  CALL "%FUN%" :INSTALL_EDITABLE
  IF ERRORLEVEL 1 GOTO :FAILED
) ELSE (
  CALL "%FUN%" :PYTHON_SETUP "%ARGUMENT%"
  IF ERRORLEVEL 1 GOTO :FAILED
)

CALL "%FUN%" :LINE_BREAK
CALL "%FUN%" :PRINT_LINE "   End of the make execution"
CALL "%FUN%" :LINE_BREAK

CHOICE /C YN /M "Do it again ? (Y/N)"
IF ERRORLEVEL 2 GOTO :EOF
GOTO :STARTAGAIN

:FAILED
CALL "%FUN%" :LINE_BREAK
CALL "%FUN%" :PRINT_LINE "   ERROR: make execution failed (action=%ARGUMENT%)"
CALL "%FUN%" :LINE_BREAK
EXIT /B 1

:EOF
EXIT /B 0
