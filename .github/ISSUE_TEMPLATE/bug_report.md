---
name: Bug report
about: Fix something that's not working
title: ''
labels: 'alert: NEED MORE DEFINITION, type: bug'
assignees: ''

---

*Replace italics below with details for this issue.*

## Describe the Problem ##
*Provide a clear and concise description of the bug here.*

### Expected Behavior ###
*Provide a clear and concise description of what you expected to happen here.*

### Environment ###
Describe your runtime environment:
*1. Machine: (e.g. HPC name, Linux Workstation, Mac Laptop)*
*2. OS: (e.g. RedHat Linux, MacOS)*
*3. Software version number(s)*

### To Reproduce ###
Describe the steps to reproduce the behavior:
*1. Go to '...'*
*2. Click on '....'*
*3. Scroll down to '....'*
*4. See error*

### Relevant Deadlines ###
*List relevant project deadlines here or state NONE.*

## Define the Metadata ##

### Assignee ###
- [ ] Select **engineer(s)** or **no engineer** required
- [ ] Select **scientist(s)** or **no scientist** required

### Labels ###
- [ ] Select **component(s)**
- [ ] Select **priority**

### Projects and Milestone ###
- [ ] Select first **Project** for support of the current release
- [ ] Select second **Project** for development toward the next official release
- [ ] Select **Milestone** as the next bugfix version

## Bugfix Checklist ##
- [ ] Complete the issue definition above, including the **Time Estimate** and **Funding Source**.
- [ ] Fork this repository or create a branch of **main_\<Version>**.
Branch name: `bugfix_<Issue Number>/main_<Version>_<Description>`
- [ ] Fix the bug and test your changes.
- [ ] Add/update log messages for easier debugging.
- [ ] Add/update tests.
- [ ] Add/update documentation.
- [ ] Push local changes to GitHub.
- [ ] Submit a pull request to merge into **main_\<Version>**.
Pull request: `bugfix <Issue Number> main_<Version> <Description>`
- [ ] Define the pull request metadata, as permissions allow.
Select: **Reviewer(s)** and **Development** issue
Select: **Project** for support of the current release
Select: **Milestone** as the next bugfix version
- [ ] Iterate until the reviewer(s) accept and merge your changes.
- [ ] Delete your fork or branch.
- [ ] Complete the steps above to fix the bug on the **develop** branch.
Branch name:  `bugfix_<Issue Number>/develop_<Description>`
Pull request: `bugfix <Issue Number> develop <Description>`
Select: **Reviewer(s)** and **Development** issue
Select: **Project** for the next official release
Select: **Milestone** as the next official version
- [ ] Close this issue.
