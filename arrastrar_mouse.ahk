SendMode("Event")
CoordMode("Mouse", "Screen")

x_start := A_Args[1] + 0
y_start := A_Args[2] + 0
x_end   := A_Args[3] + 0
y_end   := A_Args[4] + 0

duration := 200
steps := 25

dx := (x_end - x_start)/steps
dy := (y_end - y_start)/steps
sleep_time := duration/steps

MouseMove(x_start, y_start, 0)
Sleep 300
Click("L", "Down")
Loop steps {
    MouseMove(x_start + dx*A_Index, y_start + dy*A_Index, 0)
    Sleep sleep_time
}
Click("L", "Up")

Sleep 400
