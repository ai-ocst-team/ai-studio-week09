============================= test session starts =============================
platform win32 -- Python 3.13.15, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\sinbi\ai_studio\venv1\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\sinbi\ai_studio\ai-studio-week09
collecting 5 items                                                          collected 5 items                                                              

test/test_integration.py::test_happy_path PASSED                         [ 20%]
test/test_integration.py::test_empty_folder PASSED                       [ 40%]
test/test_integration.py::test_corrupted_image PASSED                    [ 60%]
test/test_integration.py::test_missing_exif PASSED                       [ 80%]
test/test_integration.py::test_continues_after_image_error PASSED        [100%]

============================== warnings summary ===============================
test/test_integration.py::test_happy_path
test/test_integration.py::test_happy_path
test/test_integration.py::test_missing_exif
test/test_integration.py::test_continues_after_image_error
test/test_integration.py::test_continues_after_image_error
  C:\Users\sinbi\ai_studio\ai-studio-week09\prepare_photo\prepare_photo.py:69: DeprecationWarning: Image.Image.getdata is deprecated and will be removed in Pillow 14 (2027-10-15). Use get_flattened_data instead.
    pixels = list(small.getdata())

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 5 passed, 5 warnings in 6.31s ========================