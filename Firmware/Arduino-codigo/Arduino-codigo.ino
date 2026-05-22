// ==========================================
// FIRMWARE: MÚSCULOS DEL ROVER (Arduino Uno)
// ==========================================

// --- 1. PINES DEL PUENTE H (L298N) ---
// Motor Izquierdo
const int ENA = 5;  // Pin PWM (debe tener el símbolo ~ en el Arduino)
const int IN1 = 7;  // Dirección 1
const int IN2 = 8;  // Dirección 2

// Motor Derecho
const int ENB = 6;  // Pin PWM (debe tener el símbolo ~ en el Arduino)
const int IN3 = 9;  // Dirección 1
const int IN4 = 10; // Dirección 2

// --- 2. PIN DE LA ALARMA MÉDICA ---
const int PIN_BUZZER = 11;

// Velocidad base de los motores (Rango: 0 a 255)
// 150 es una velocidad estable para que la cámara no tiemble demasiado
int velocidad = 150; 

void setup() {
  // Abrir el canal de comunicación con el Cerebro (Python)
  Serial.begin(9600);

  // Configurar todos los pines como salida (Músculos)
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  
  pinMode(PIN_BUZZER, OUTPUT);

  // Bloqueo de seguridad: Iniciar con motores apagados
  detenerMotores();
}

void loop() {
  // ¿Python nos mandó una letra por el cable USB?
  if (Serial.available() > 0) {
    char comando = Serial.read();

    // Máquina de estados
    switch (comando) {
      case 'A': // Avanzar
        noTone(PIN_BUZZER);
        avanzar();
        break;
        
      case 'S': // Reversa
        noTone(PIN_BUZZER);
        reversa();
        break;
        
      case 'D': // Derecha
        noTone(PIN_BUZZER);
        girarDerecha();
        break;
        
      case 'I': // Izquierda
        noTone(PIN_BUZZER);
        girarIzquierda();
        break;

      case 'P': // Paro Total (Standby)
        noTone(PIN_BUZZER);
        detenerMotores();
        break;
        
      case 'E': // EMERGENCIA (IA detectó paciente caído)
        detenerMotores();       // 1. Frenar en seco
        tone(PIN_BUZZER, 1000); // 2. Disparar alarma a 1000 Hz
        break;
    }
  }
}

// ==========================================
// FUNCIONES DE TRACCIÓN DIFERENCIAL
// ==========================================

void avanzar() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, velocidad);
  analogWrite(ENB, velocidad);
}

void reversa() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  analogWrite(ENA, velocidad);
  analogWrite(ENB, velocidad);
}

void girarIzquierda() {
  // Llanta Izquierda en reversa, Llanta Derecha hacia adelante
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, velocidad);
  analogWrite(ENB, velocidad);
}

void girarDerecha() {
  // Llanta Izquierda hacia adelante, Llanta Derecha en reversa
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  analogWrite(ENA, velocidad);
  analogWrite(ENB, velocidad);
}

void detenerMotores() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
}