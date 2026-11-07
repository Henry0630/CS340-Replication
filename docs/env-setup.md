# 环境交接：在有 Docker 的机器上跑一遍（约 30 分钟）

> 背景：B（张歆海）这台 Windows 机器没有也不打算装 Docker / WSL。Dockerfile 已经写好，
> 但**必须在一台有 Docker 的机器上真跑一遍**才算验证，跑完把下面「回传清单」的东西发回来，
> B 填进 `docs/environment.md` 并提交。

## 0 前置检查（2 分钟）

```bash
docker --version          # 需要 Docker 20.10+，建议 Desktop 4.x
docker info --format '{{.OSType}} {{.Architecture}} {{.ServerVersion}}'
```

期望：`linux amd64`（必须是 **linux**，Windows 容器不行）。
不满足就先按第 5 节排查。

## 1 构建镜像（10–20 分钟，第一次要拉基础镜像）

```bash
git clone <你的仓库地址> cs340-repro
cd cs340-repro
time docker build --build-arg GO_IMAGE=golang:1.22.4-bookworm -t cs340-repro:go1.22 .
```

构建过程里会跑一次冒烟测试（`-race` 编译 + goroutine/channel 程序），
最后一行应看到 `smoke ok 1` 和 `go version go1.22.4 linux/amd64`。

**失败的话把最后 30 行贴回来**，常见原因见第 5 节。

## 2 记录环境（2 分钟）

```bash
docker run --rm cs340-repro:go1.22 sh -c 'uname -a; \
  go version; go env GOOS GOARCH GOVERSION GOMAXPROCS CGO_ENABLED; \
  gcc --version | head -1; cat /etc/os-release | head -2'
docker image inspect cs340-repro:go1.22 --format '{{index .RepoDigests 0}}'
docker images cs340-repro:go1.22 --format '{{.Size}}'
```

## 3 构建 Go 1.21 版本（Extension 对照组，5 分钟）

```bash
time docker build --build-arg GO_IMAGE=golang:1.21.13-bookworm -t cs340-repro:go1.21 .
docker images | grep cs340-repro
```

两个镜像**只有 Go 版本不同**，这是 Extension 的唯一变量；别再动别的。

## 4 跑通一次真实使用（5 分钟）

```bash
mkdir -p /tmp/probe && cd /tmp/probe
docker run --rm -v "$PWD:/work" -w /work cs340-repro:go1.22 bash -c '
  cat > main.go <<EOF
package main

import ("fmt"; "sync")

func main() {
    var wg sync.WaitGroup
    x := 0
    for i := 0; i < 4; i++ {
        wg.Add(1)
        go func() { defer wg.Done(); x++ }()   // 故意数据竞争
    }
    wg.Wait()
    fmt.Println("x =", x)
}
EOF
  go mod init probe >/dev/null 2>&1
  go run -race main.go 2>&1 | tail -5
'
```

期望：输出里有 `WARNING: DATA RACE`。**看不到 DATA RACE 就说明 `-race` 没生效**，
别继续，先修环境。

## 5 排查

| 症状 | 原因 / 处理 |
|---|---|
| `docker info` 显示 `windows` | 用了 Windows 容器模式：Docker Desktop → 右键托盘 → Switch to Linux containers |
| `docker: command not found` | 没装 Docker；Windows 上装 Docker Desktop（会自动装 WSL2 后端，需重启一次） |
| 构建时报 `failed to solve: ... no space left on device` | 镜像盘空间不足：Docker Desktop → Settings → Resources 换盘，至少留 8 GB |
| `gcc: not found` 或 cgo 报错 | 基础镜像换过？必须用 `golang:*-bookworm`（含 gcc），不要用 `alpine` |
| `go: downloading toolchain go1.x` | `GOTOOLCHAIN=local` 没生效：确认用的是本仓库的 Dockerfile，不要自己改 |
| 构建很慢 | 首次拉基础镜像正常；之后有层缓存。国内网络可在 Docker Desktop 里配置镜像加速 |
| Linux 主机上 `permission denied /var/run/docker.sock` | `sudo usermod -aG docker $USER` 后重新登录 |

## 6 回传清单（发这 6 项给 B）

1. `docker --version` 与 `docker info --format '{{.OSType}} {{.Architecture}}'`
2. 第 2 节 `uname -a` 整行（内核版本写进报告）
3. `go version` 与 `go env GOOS GOARCH GOVERSION GOMAXPROCS CGO_ENABLED`
4. `gcc --version | head -1`
5. 基础镜像 digest（`RepoDigests` 那一行）与镜像大小
6. 两次 `time docker build` 的耗时（README 要写"预期运行时间"）

## 7 B 收到后要做的事

1. 把 2–6 项填进 `docs/environment.md` 的 L2 表格；
2. 把 digest 写进 `Dockerfile` 顶部注释，并把 `ARG GO_IMAGE=golang:1.22.4-bookworm`
   换成 `golang@sha256:...`（钉死到摘要，tag 被上游改了也不影响）；
3. 提交：`env: pin experiment image by digest and record kernel/go versions (1240012291 张歆海)`；
4. 在 PR 里 @C，告诉他已经可以用 `cs340-repro:go1.22` 跑复现器了。
