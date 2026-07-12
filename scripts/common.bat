@ECHO OFF
REM ===========================================================================
REM                   Author: Florent TOURNOIS | License: MIT
REM ===========================================================================
SETLOCAL EnableExtensions

FOR %%I IN ("%~dp0..") DO SET "REPO_ROOT=%%~fI"
CD /D "%REPO_ROOT%" || (ECHO ERROR: cannot enter "%REPO_ROOT%" & EXIT /B 1)

IF "%~1"=="" (
  ECHO Usage: %~nx0 ^<COMMAND^> [args...]
  EXIT /B 2
)

SET "CMD=%~1"
IF "%CMD:~0,1%"==":" SET "CMD=%CMD:~1%"
SHIFT

SET "VALID_CMD="
FOR %%C IN (
  PRINT_LINE CONFIGURE_DISPLAY CLEAR_SCREEN LINE_BREAK INIT_PYTHON GET_PYTHON
  INSTALL_REQUIREMENTS INSTALL_EDITABLE PYTHON_LAUNCHER PYTHON_FROM_MAKE
  RUN_TESTS RUN_SPHINX RUN_DOXYGEN RUN_BUILD RUN_CLEAN RELEASE_CHECK
  BUMP_VERSION TAG_VERSION AUDIT_TAGS
) DO IF /I "%CMD%"=="%%C" SET "VALID_CMD=1"

IF NOT DEFINED VALID_CMD (
  ECHO ERROR: Unknown common command: "%CMD%".
  EXIT /B 2
)

CALL :%CMD% %1 %2 %3 %4 %5 %6 %7 %8 %9
EXIT /B %ERRORLEVEL%

:PRINT_LINE
ECHO(%~1
EXIT /B 0

:CONFIGURE_DISPLAY
CHCP 65001 >NUL 2>&1
EXIT /B 0

:CLEAR_SCREEN
CLS
EXIT /B 0

:LINE_BREAK
ECHO --------------------------------------------------------------------------
EXIT /B 0

:INIT_PYTHON
IF /I "%PYTHON_READY%"=="1" EXIT /B 0
SET "VENV_DIR=%REPO_ROOT%\.venv"
SET "PYTHON=%VENV_DIR%\Scripts\python.exe"

IF NOT EXIST "%PYTHON%" (
  python.exe -V >NUL 2>&1
  IF ERRORLEVEL 1 (
    ECHO ERROR: python.exe is required to create "%VENV_DIR%".
    EXIT /B 1
  )
  python.exe -m venv "%VENV_DIR%"
  IF ERRORLEVEL 1 EXIT /B 1
)

IF NOT EXIST "%PYTHON%" (
  ECHO ERROR: Virtual environment Python not found: "%PYTHON%".
  EXIT /B 1
)
SET "PYTHON_READY=1"
EXIT /B 0

:GET_PYTHON
CALL :INIT_PYTHON
IF ERRORLEVEL 1 EXIT /B 1
ECHO %PYTHON%
EXIT /B 0

:INSTALL_REQUIREMENTS
CALL :INIT_PYTHON
IF ERRORLEVEL 1 EXIT /B 1
SET "REQUIRE_FILE=%~1"
IF "%REQUIRE_FILE%"=="" (
  ECHO ERROR: Missing requirements file.
  EXIT /B 2
)
IF NOT EXIST "%REQUIRE_FILE%" (
  ECHO ERROR: Requirements file not found: "%REQUIRE_FILE%".
  EXIT /B 2
)
"%PYTHON%" -m pip install -r "%REQUIRE_FILE%"
EXIT /B %ERRORLEVEL%

:INSTALL_EDITABLE
CALL :INIT_PYTHON
IF ERRORLEVEL 1 EXIT /B 1
"%PYTHON%" -m pip install --editable ".[dev,docs]"
EXIT /B %ERRORLEVEL%

:PYTHON_LAUNCHER
CALL :INIT_PYTHON
IF ERRORLEVEL 1 EXIT /B 1
IF "%~1"=="" (
  ECHO ERROR: Missing Python script.
  EXIT /B 2
)
IF NOT EXIST "%~1" (
  ECHO ERROR: Python script not found: "%~1".
  EXIT /B 2
)
"%PYTHON%" "%~1" %2 %3 %4 %5 %6 %7 %8 %9
EXIT /B %ERRORLEVEL%

:PYTHON_FROM_MAKE
IF /I NOT "%~1"=="python" (
  ECHO ERROR: PYTHON_FROM_MAKE expects the first argument "python".
  EXIT /B 2
)
CALL :PYTHON_LAUNCHER "%~2" %3 %4 %5 %6 %7 %8 %9
EXIT /B %ERRORLEVEL%

:RUN_TESTS
CALL :INIT_PYTHON
IF ERRORLEVEL 1 EXIT /B 1
"%PYTHON%" -m pytest
EXIT /B %ERRORLEVEL%

:RUN_SPHINX
CALL :INIT_PYTHON
IF ERRORLEVEL 1 EXIT /B 1
"%PYTHON%" -m sphinx.cmd.build -b html -W --keep-going docs docs\_build\html
EXIT /B %ERRORLEVEL%

:RUN_DOXYGEN
WHERE doxygen.exe >NUL 2>&1
IF ERRORLEVEL 1 (
  ECHO ERROR: doxygen.exe is not available in PATH.
  EXIT /B 1
)
doxygen.exe docs\config_doc.dox
EXIT /B %ERRORLEVEL%

:RUN_BUILD
CALL :INIT_PYTHON
IF ERRORLEVEL 1 EXIT /B 1
"%PYTHON%" scripts\release.py build --allow-dirty
EXIT /B %ERRORLEVEL%

:RUN_CLEAN
IF EXIST build RMDIR /S /Q build
IF EXIST dist RMDIR /S /Q dist
IF EXIST docs\_build RMDIR /S /Q docs\_build
EXIT /B 0

:RELEASE_CHECK
CALL :INIT_PYTHON
IF ERRORLEVEL 1 EXIT /B 1
"%PYTHON%" scripts\release.py check
EXIT /B %ERRORLEVEL%

:BUMP_VERSION
CALL :INIT_PYTHON
IF ERRORLEVEL 1 EXIT /B 1
IF "%~1"=="" (
  "%PYTHON%" scripts\release.py bump patch
) ELSE (
  "%PYTHON%" scripts\release.py bump "%~1"
)
EXIT /B %ERRORLEVEL%

:TAG_VERSION
CALL :INIT_PYTHON
IF ERRORLEVEL 1 EXIT /B 1
"%PYTHON%" scripts\release.py tag
EXIT /B %ERRORLEVEL%

:AUDIT_TAGS
CALL :INIT_PYTHON
IF ERRORLEVEL 1 EXIT /B 1
"%PYTHON%" scripts\release.py audit-tags
EXIT /B %ERRORLEVEL%
