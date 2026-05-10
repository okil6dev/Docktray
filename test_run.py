import traceback
import sys

try:
    import main
    main.main()
except Exception as e:
    with open("crash.txt", "w") as f:
        traceback.print_exc(file=f)
    print("Caught exception:", e)
