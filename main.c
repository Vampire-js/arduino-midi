#define F_CPU 16000000UL

#include <avr/io.h>
#include <util/delay.h>
#include <stdint.h>

void uart_init(void) {
    // 9600 baud at 16 MHz
    UBRR0H = 0;
    UBRR0L = 103;

    // Enable transmitter
    UCSR0B = (1 << TXEN0);

    // 8-bit data, 1 stop bit
    UCSR0C = (1 << UCSZ01) | (1 << UCSZ00);
}

void uart_char(char c) {
    while (!(UCSR0A & (1 << UDRE0)));
    UDR0 = c;
}

void uart_string(const char *s) {
    while (*s) {
        uart_char(*s++);
    }
}

int main(void) {
    uart_init();

    // D7 (PD7): output, drive LOW
    DDRD |= (1 << PD7);
    PORTD &= ~(1 << PD7);

    // D4 (PD4): input with pull-up
    DDRD &= ~(1 << PD4);
    PORTD |= (1 << PD4);

    uint8_t previous = 0;

    while (1) {
        uint8_t pressed = !(PIND & (1 << PD4));

        if (pressed != previous) {
            _delay_ms(20); // Debounce

            pressed = !(PIND & (1 << PD4));

            if (pressed != previous) {
                if (pressed) {
                    uart_string("1,1,1\r\n");
                } else {
                    uart_string("1,1,0\r\n");
                }

                previous = pressed;
            }
        }
    }
}