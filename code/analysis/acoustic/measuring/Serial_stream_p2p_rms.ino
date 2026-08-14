const uint8_t MIC_PIN_0 = A0;
const uint8_t MIC_PIN_1 = A1;
const uint16_t WINDOW_MS = 20;

void setup() {
  Serial.begin(115200);
}

void loop() {
  uint32_t t_start = millis();
  uint16_t vmin_0 = 1023, vmax_0 = 0;
  uint16_t vmin_1 = 1023, vmax_1 = 0;
  uint32_t sum_0 = 0, sum_1 = 0;
  uint32_t sum_sq_0 = 0, sum_sq_1 = 0;
  uint32_t n = 0;

  while (millis() - t_start < WINDOW_MS) {
    uint16_t v_0 = analogRead(MIC_PIN_0);
    uint16_t v_1 = analogRead(MIC_PIN_1);

    if(v_0 < vmin_0) vmin_0 = v_0;
    if(v_1 < vmin_1) vmin_1 = v_1;

    if(v_0 > vmax_0) vmax_0 = v_0;
    if(v_1 > vmax_1) vmax_1 = v_1;

    sum_0 += v_0;
    sum_1 += v_1;
    sum_sq_0 += (uint32_t)v_0 * v_0;
    sum_sq_1 += (uint32_t)v_1 * v_1;
    n++;
  }

  float avg_0 = (float)sum_0 / n;
  float avg_1 = (float)sum_1 / n;

  // variance = mean(x^2) - mean(x)^2, computed in one pass (no sample
  // buffer needed); clamp to 0 in case float rounding makes it slightly
  // negative for a near-silent/constant window.
  float var_0 = (float)sum_sq_0 / n - avg_0 * avg_0;
  float var_1 = (float)sum_sq_1 / n - avg_1 * avg_1;
  if (var_0 < 0) var_0 = 0;
  if (var_1 < 0) var_1 = 0;

  float rms_0 = sqrt(var_0);
  float rms_1 = sqrt(var_1);

  // t_ms, vmax, vmin, rms, sample count
  Serial.print(t_start); Serial.print(',');
  Serial.print(vmax_0); Serial.print(',');
  Serial.print(vmin_0); Serial.print(',');
  Serial.print(rms_0); Serial.print(',');
  Serial.print(vmax_1); Serial.print(',');
  Serial.print(vmin_1); Serial.print(',');
  Serial.print(rms_1); Serial.print(',');
  Serial.println(n);
}
