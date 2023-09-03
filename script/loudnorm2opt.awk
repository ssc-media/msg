#! /bin/awk -f

/Input Integrated:/ { printf("measured_I=%s:", $3) }
/Input True Peak:/ { printf("measured_TP=%s:", $4) }
/Input LRA:/ { printf("measured_LRA=%s:", $3) }
/Input Threshold:/ { printf("measured_thresh=%s:", $3) }
/Target Offset:/ { printf("offset=%s\n", $3) }
