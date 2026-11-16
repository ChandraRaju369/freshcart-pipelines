# Part A: Git & CI/CD Technical Reference

## A1. Four-Stage Git Architecture & Lifecycle
In Git, code moves through four distinct areas:

```
+--------------------+         git add          +-------------------+
|  Working Directory |  --------------------->  |   Staging Area    |
| (Local file system)|                          |     (Index)       |
+--------------------+                          +-------------------+
                                                          |
                                                          | git commit
                                                          v
+--------------------+        git push          +-------------------+
| Remote Repository  |  <---------------------  | Local Repository  |
|  (GitHub / Cloud)  |  --------------------->  |     (.git/)       |
+--------------------+        git pull          +-------------------+
```

1. **Working Directory (Working Tree):** The actual sandbox on your local file system where files are created, viewed, and modified. Changes here are untracked until explicitly staged.
2. **Staging Area (Index):** An intermediate holding buffer that prepares and curates the exact snapshot of files to be included in the next commit.
3. **Local Repository (`.git/`):** The local database storing the permanent history of all committed snapshots (commits, trees, and blobs) stored safely on your machine.
4. **Remote Repository (GitHub):** The centralized cloud-hosted repository accessible by teammates for collaboration, CI/CD triggering, and team synchronization.

---

## A2. Git Command Lifecycle Table

| Command | Where the change happens | What exactly happens? |
| :--- | :--- | :--- |
| `git init` | Working Directory & Local File System | Creates an empty `.git` metadata directory in the current folder, initializing it as a Git version-controlled repository. |
| `git add train.py` | Staging Area (Index) | Copies the current state of `train.py` from the working directory into the staging area, marking it to be included in the next commit snapshot. |
| `git commit -m "msg"` | Local Repository (`.git/`) | Takes all changes staged in the index, seals them into an immutable commit object with an author timestamp and commit message, and updates the local branch pointer. |
| `git remote add origin URL` | Git Configuration (`.git/config`) | Registers a named reference (`origin`) mapped to the remote repository URL, defining the default upstream destination for push and fetch operations. |
| `git push -u origin main` | Remote Repository (GitHub) | Uploads all local `main` branch commits to the remote server at `origin` and configures the local branch to track the remote branch. |
| `git pull origin main` | Local Repository and Working Directory | Fetches new commits from the remote `main` branch and immediately merges them into the active local branch in your working directory. |

---

### Critical Question: Can your teammate see your code on GitHub after running `git commit`? Why or why not?

**Answer:**  
**No, your teammate cannot see your code on GitHub after running `git commit`.**

**Why:**  
`git commit` operates **strictly within your local repository** (`.git/` directory on your local disk). It packages the staged changes into a new local commit object and updates your local branch pointer, but **zero network communication occurs**. Your code only becomes visible to teammates and CI/CD runners after you execute `git push`, which transmits the commit objects over HTTPS/SSH to the remote server (GitHub).
