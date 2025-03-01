from .src import run
try: 

    if __name__ == "__main__":
        run()
except KeyboardInterrupt:
    print("\nProgram interrupted by user. Exiting gracefully...")