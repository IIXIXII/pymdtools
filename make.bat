@ECHO OFF
REM ===========================================================================
REM                   Author: Florent TOURNOIS | License: MIT
REM ===========================================================================
SETLOCAL EnableExtensions

SET "REPO_ROOT=%~dp0"
CD /D "%REPO_ROOT%" || (ECHO ERROR: cannot enter "%REPO_ROOT%" & EXIT /B 1)
SET "MODULE=pymdtools"
SET "COMMON=%REPO_ROOT%scripts\common.bat"
SET "ACTION=%~1"

IF "%ACTION%"=="" GOTO :USAGE
IF NOT EXIST "%COMMON%" (
  ECHO ERROR: common script not found: "%COMMON%".
  EXIT /B 1
)

IF EXIST "%REPO_ROOT%%MODULE%\version.bat" CALL "%REPO_ROOT%%MODULE%\version.bat"
ECHO [%MODULE% %VERSION%] %ACTION%

IF /I "%ACTION%"=="requirements" (
  CALL "%COMMON%" INSTALL_REQUIREMENTS requirements.txt
  GOTO :RESULT
)
IF /I "%ACTION%"=="requirements-dev" (
  CALL "%COMMON%" INSTALL_REQUIREMENTS requirements-dev.txt
  GOTO :RESULT
)
IF /I "%ACTION%"=="requirements-docs" (
  CALL "%COMMON%" INSTALL_REQUIREMENTS requirements-docs.txt
  GOTO :RESULT
)
IF /I "%ACTION%"=="install_editable" (
  CALL "%COMMON%" INSTALL_EDITABLE
  GOTO :RESULT
)
IF /I "%ACTION%"=="test" (
  CALL "%COMMON%" RUN_TESTS
  GOTO :RESULT
)
IF /I "%ACTION%"=="sphinx" (
  CALL "%COMMON%" RUN_SPHINX
  GOTO :RESULT
)
IF /I "%ACTION%"=="doxygen" (
  CALL "%COMMON%" RUN_DOXYGEN
  GOTO :RESULT
)
IF /I "%ACTION%"=="build" (
  CALL "%COMMON%" RUN_BUILD
  GOTO :RESULT
)
IF /I "%ACTION%"=="clean" (
  CALL "%COMMON%" RUN_CLEAN
  GOTO :RESULT
)
IF /I "%ACTION%"=="check" (
  CALL "%COMMON%" RELEASE_CHECK
  GOTO :RESULT
)
IF /I "%ACTION%"=="increase_version" (
  CALL "%COMMON%" BUMP_VERSION "%~2"
  GOTO :RESULT
)
IF /I "%ACTION%"=="tag_version" (
  CALL "%COMMON%" TAG_VERSION
  GOTO :RESULT
)
IF /I "%ACTION%"=="audit_tags" (
  CALL "%COMMON%" AUDIT_TAGS
  GOTO :RESULT
)
IF /I "%ACTION%"=="python" (
  CALL "%COMMON%" PYTHON_FROM_MAKE %*
  GOTO :RESULT
)
IF /I "%ACTION%"=="upload" (
  ECHO ERROR: Local upload is disabled. Publish a verified GitHub release instead.
  EXIT /B 2
)

ECHO ERROR: Unknown action "%ACTION%".
GOTO :USAGE

:RESULT
EXIT /B %ERRORLEVEL%

:USAGE
ECHO Usage: %~nx0 ^<action^>
ECHO.
ECHO Actions:
ECHO   requirements requirements-dev requirements-docs install_editable
ECHO   test sphinx doxygen build clean check audit_tags
ECHO   increase_version [major^|minor^|patch] tag_version
ECHO   python ^<script.py^> [args...]
EXIT /B 2
