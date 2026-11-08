#!/bin/bash

#set -e
#set -x

if [ ! -f ~/.config/fritz_solar.cfg ]; then
  echo "Config missing"
  exit 127
fi

while IFS='=' read -r key value; do
    # Skip empty lines and comments
    [[ -z "$key" || "$key" =~ ^# ]] && continue
    # Remove quotes if present
    value="${value%\"}"
    value="${value#\"}"
    declare "$key=$value"
done < ~/.config/fritz_solar.cfg

if [ -f ${TMP_FILE} ]; then
  if ! test $(find "${TMP_FILE}" -mmin +${CACHE_MINS}); then
      CACHE=$(cat ${TMP_FILE})
      echo ${CACHE}
      exit 0
  fi
fi

CHALLENGE_XML=$(curl -m 10 -k -s "$FRITZ_URL/login_sid.lua")
if [[ -z ${CHALLENGE_XML} ]]; then
    echo "N/A"
    exit 1
fi

CHALLENGE=$(echo "$CHALLENGE_XML" | xmllint --xpath 'string(//Challenge)' -)
RESPONSE=$(echo -n "${CHALLENGE}-${PASSWORD}" | iconv -f UTF-8 -t UTF-16LE | md5sum | cut -d' ' -f1)

SID_XML=$(curl -m 10 -k -s "${FRITZ_URL}/login_sid.lua?username=${USERNAME}&response=${CHALLENGE}-${RESPONSE}")
SID=$(echo "$SID_XML" | xmllint --xpath 'string(//SID)' -)

if [ ${SID} != "0000000000000000" ] && [ -n ${SID} ]; then
    AIN_XML=$(echo "${AIN}" | sed 's/.\{5\}/& /')
    DEVICES_XML=$(curl -m 10 -k -s "${FRITZ_URL}/webservices/homeautoswitch.lua?sid=${SID}&ain=${AIN}&switchcmd=getdevicelistinfos")

    #echo ${DEVICES_XML}

    POWER_MW=$(echo "$DEVICES_XML" | xmllint --xpath "string(//device[contains(@identifier, '$AIN_XML')]/powermeter/power)" -)

    if [[ -z "${POWER_MW}" ]]; then
        echo "N/A"
        exit 2
    fi

    POWER_W=$(echo "scale=0; $POWER_MW / 1000" | bc)

    TEMP_C=$(echo "$DEVICES_XML" | xmllint --xpath "string(//device[contains(@identifier, '$AIN_XML')]/temperature/celsius)" -)

    if [[ -z "${TEMP_C}" ]]; then
        echo "N/A"
        exit 2
    fi

    TEMP_C=$(echo "scale=0; $TEMP_C / 10" | bc)

    if [ -z ${POWER_W} ]; then
        POWER_W="-"
    fi
    if [ -z ${TEMP_C} ]; then
        TEMP_C="-"
    fi

    printf "%dW " "${POWER_W}"
    printf "%d\u00B0C\n" "${TEMP_C}"

    printf "%dW " "${POWER_W}" > ${TMP_FILE}
    printf "%d\u00B0C\n" "${TEMP_C}" >> ${TMP_FILE}

else
    echo "SID is invalid"
    exit 3
fi
