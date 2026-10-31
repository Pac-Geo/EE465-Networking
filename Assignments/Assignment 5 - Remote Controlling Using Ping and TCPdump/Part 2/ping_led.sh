
#!/usr/bin/env bash
# EE465 - Remote LED Control using tcpdump

IFACE="${1:-tailscale0}"
PIN=17

# Initialize LED off
pinctrl set "$PIN" op dl

watch_pings() {
    local action="$1"
    local filter="$2"

    tcpdump -i "$IFACE" -nn -l -s 0 "$filter" |
    while IFS= read -r line; do
        [[ "$line" == *"ICMP echo request"* ]] || continue

        case "$action" in
            on)
                pinctrl set "$PIN" op dh
                echo "PING aaae -> LED ON"
                ;;
            off)
                pinctrl set "$PIN" op dl
                echo "PING abae -> LED OFF"
                ;;
            other)
                echo "PING received -> no action"
                ;;
        esac
    done
}

watch_pings on \
    'icmp and icmp[0] = 8 and icmp[16:2] = 0xaaae' &
PID_ON=$!

watch_pings off \
    'icmp and icmp[0] = 8 and icmp[16:2] = 0xabae' &
PID_OFF=$!

watch_pings other \
    'icmp and icmp[0] = 8 and not (icmp[16:2] = 0xaaae or icmp[16:2] = 0xabae)' &
PID_OTHER=$!

cleanup() {
    trap - EXIT
    for pid in "$PID_ON" "$PID_OFF" "$PID_OTHER"; do
        pkill -TERM -P "$pid" 2>/dev/null
        kill "$pid" 2>/dev/null
    done
    pinctrl set "$PIN" op dl
    echo "Stopped."
}

trap cleanup EXIT
trap 'exit 130' INT TERM

echo "Listening for pings on $IFACE"
echo "aaae = ON | abae = OFF"
echo "Press Ctrl+C to stop."

wait
