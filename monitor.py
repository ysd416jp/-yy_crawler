import os
def main():
    # 1. 複数の可能性のある名前で環境変数をチェック
    names = ["GCP_JSON", "GOOGLE_SERVICE_ACCOUNT_JSON"]
    for name in names:
        val = os.environ.get(name, "")
        print(f"Check {name}: length={len(val)}")
        if len(val) > 0:
            print(f"-> Found! starts with: {val[:10]}...")

if __name__ == "__main__":
    main()
