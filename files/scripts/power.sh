#!/bin/bash

BATTERY="/org/freedesktop/UPower/devices/battery_BAT0"

# Check if upower is installed
if ! command -v upower &> /dev/null; then
    echo '{"error": "upower command not found", "resolution": "apt install upower"}'
    exit 1
fi

# Check if device exists
if ! upower -e | grep -q "${BATTERY}"; then
    DEVICES=$(upower -e | jq -R -s 'split("\n") | map(select(length > 0))')
    echo '{"error": "Device not found", "device": "'${BATTERY}'", "available devices": '${DEVICES}'}'
    #echo "Available devices:" >&2
    #upower -e >&2
    exit 1
fi

case ${1} in
  "icon")
    RESULT=$(upower -i ${BATTERY} | grep "icon-name:" | awk '{print $2}' | sed "s/'//g")
  ;;
  "state")
    RESULT=$(upower -i ${BATTERY} | grep "state:" | awk '{print $2}')
  ;;
  "time")
    RESULT=$(upower -i ${BATTERY} | grep "time" | awk '{print $4 " " $5}')
  ;;
  "percentage")
    RESULT=$(upower -i ${BATTERY} | grep "percentage:" | awk '{print $2}')
  ;;
  "energy")
    RESULT=$(upower -i ${BATTERY} | grep "energy:" | awk '{print $2 " " $3}')
  ;;
  "energy-full")
    RESULT=$(upower -i ${BATTERY} | grep "energy-full:" | awk '{print $2 " " $3}')
  ;;
  "energy-empty")
    RESULT=$(upower -i ${BATTERY} | grep "energy-empty:" | awk '{print $2 " " $3}')
  ;;
  "energy-rate")
    RESULT=$(upower -i ${BATTERY} | grep "energy-rate:" | awk '{print $2 " " $3}')
  ;;
  "cycles")
    RESULT=$(upower -i ${BATTERY} | grep "cycles:" | awk '{print $2}')
  ;;
  "capacity")
    RESULT=$(upower -i ${BATTERY} | grep "capacity:" | awk '{print $2}')
  ;;
  "technology")
    RESULT=$(upower -i ${BATTERY} | grep "technology:" | awk '{print $2}')
  ;;
  "warning")
    RESULT=$(upower -i ${BATTERY} | grep "warning-level:" | awk '{print $2}')
  ;;
  "voltage")
    RESULT=$(upower -i ${BATTERY} | grep "voltage:" | awk '{print $2 " " $3}')
  ;;
  "battery")
    upower -e
    exit 0
  ;;
  "json")
    RESULT=$(upower -i ${BATTERY} | jq -Rn 'reduce (inputs | capture("^[[:space:]]*(?<key>[^:]+)[[:space:]]*:[[:space:]]*(?<value>.*)")) as $match ({}; .[$match.key] = $match.value)')
    RESULT=$(echo ${RESULT} | jq 'with_entries(select((.key | test("^(history|has)"; "i")) | not))' )
  ;;
  *)
    cat << EOF
Unknown option.

Try:
    icon
    state
    time
    energy
    energy-full
    energy-empty
    energy-rate
    cycles
    capacity
    technology
    warning
    percentage
    voltage
    battery
EOF
  exit 1
  ;;
esac

if [ -z "${RESULT}" ]; then
    RESULT="N/A"
fi

echo ${RESULT}
