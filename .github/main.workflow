action "Run deploy script" {
  uses = "maddox/actions/ssh@master"
  args = "/opt/deploy/run"
  secrets = [
    "PRIVATE_KEY",
    "USER",
  ]
}

workflow "deploy" {
  resolves = ["ssh"]
  on = "push"
}

action "ssh" {
  uses = "maddox/actions/ssh"
  secrets = ["PUBLIC_KEY", "PRIVATE_KEY", "HOST", "USER"]
  args = "cd bggrss && git pull && sudo systemctl restart bggrss.service"
}
