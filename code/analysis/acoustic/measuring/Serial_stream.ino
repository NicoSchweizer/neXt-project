const uint8_t MIC_PIN = A0;
const uint16_t WINDOW_MS = 20;

void setup() {
  Serial.begin(115200);
}

void loop() {
  uint32_t t_start = millis();
  uint16_t vmin = 1023, vmax = 0;
  uint32_t sum = 0;
  uint32_t n = 0;

  while (millis() - t_start < WINDOW_MS) {
    uint16_t v = analogRead(MIC_PIN);
    if(v < vmin) vmin = v;
    if(v > vmax) vmax = v;
    sum += v;
    n++;
  }

  float avg = (float)sum / n;
  // t_ms, peak-to-peak, rms, sample count
  Serial.print(t_start); Serial.print(',');
  Serial.print(vmax); Serial.print(',');
  Serial.print(vmin); Serial.print(',');
  Serial.print(avg, 1); Serial.print(',');
  Serial.println(n);
}
