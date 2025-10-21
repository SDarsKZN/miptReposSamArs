import RPi.GPIO as GPIO
import time
import matplotlib.pyplot as plt

class R2R_ADC:
    def __init__(self, dynamic_range, compare_time=0.01, verbose=False):
        self.dynamic_range = dynamic_range
        self.verbose = verbose
        self.compare_time = compare_time
        
        self.bits_gpio = [26, 20, 19, 16, 13, 12, 25, 11]
        self.comp_gpio = 21

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.bits_gpio, GPIO.OUT, initial=0)
        GPIO.setup(self.comp_gpio, GPIO.IN)
    
    def __del__(self):
        """Деструктор - выставляет 0 на выход ЦАП и очищает настройки GPIO"""
        GPIO.output(self.bits_gpio, 0)
        GPIO.cleanup()
    
    def number_to_dac(self, number):
        """Подает число number на вход ЦАП"""
        binary = format(number, '08b')
        for i, pin in enumerate(self.bits_gpio):
            GPIO.output(pin, int(binary[i]))
    
    def sequential_counting_adc(self):
        """Последовательный счетный АЦП с увеличением и уменьшением для точности"""
        max_value = 255  # Максимальное значение для 8-битного ЦАП
        
        # Фаза увеличения напряжения - находим верхнюю границу
        upper_bound = max_value
        for number in range(max_value + 1):
            self.number_to_dac(number)
            time.sleep(self.compare_time)
            
            comparator_state = GPIO.input(self.comp_gpio)
            
            if self.verbose:
                print(f"UP: Number: {number}, Comparator: {comparator_state}")
            
            # Если напряжение на ЦАП превысило входное напряжение
            if comparator_state == 1:
                upper_bound = number
                break
        
        # Фаза уменьшения напряжения - находим нижнюю границу
        lower_bound = 0
        for number in range(upper_bound, -1, -1):
            self.number_to_dac(number)
            time.sleep(self.compare_time)
            
            comparator_state = GPIO.input(self.comp_gpio)
            
            if self.verbose:
                print(f"DOWN: Number: {number}, Comparator: {comparator_state}")
            
            # Когда напряжение снова станет меньше входного
            if comparator_state == 0:
                lower_bound = number
                break
        
        # Возвращаем среднее значение для большей точности
        return (upper_bound + lower_bound) // 2
    
    def get_sc_voltage(self):
        """Возвращает измеренное напряжение в Вольтах"""
        digital_value = self.sequential_counting_adc()
        voltage = (digital_value / 255) * self.dynamic_range
        return voltage


def plot_voltage_vs_time(time_data, voltage_data, max_voltage):
    """Строит график зависимости напряжения от времени"""
    plt.figure(figsize=(10, 6))
    plt.plot(time_data, voltage_data, 'b-', linewidth=2, label='Измеренное напряжение')
    plt.title('Зависимость напряжения от времени')
    plt.xlabel('Время, с')
    plt.ylabel('Напряжение, В')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.ylim(0, max_voltage * 1.1)  # +10% от максимального напряжения
    plt.xlim(0, max(time_data) if time_data else 0)
    plt.legend()
    plt.tight_layout()
    plt.show()


# Основной скрипт для измерения напряжения
if __name__ == "__main__":
    voltage_values = []
    time_values = []
    duration = 3.0  # Продолжительность измерений в секундах
    
    adc = None
    try:
        # Создаем объект ADC с измеренным динамическим диапазоном
        # ЗАМЕНИТЕ 3.3 на реально измеренное значение напряжения вашего ЦАП!
        adc = R2R_ADC(dynamic_range=3.3, verbose=False)
        
        start_time = time.time()
        print(f"Начало измерений на {duration} секунд...")
        print("Напряжение будет сначала увеличиваться, потом уменьшаться для каждого измерения")
        
        while (time.time() - start_time) < duration:
            current_time = time.time() - start_time
            voltage = adc.get_sc_voltage()
            
            voltage_values.append(voltage)
            time_values.append(current_time)
            
            print(f"Время: {current_time:.2f} с, Напряжение: {voltage:.2f} В")
            time.sleep(0.1)  # Пауза между измерениями
        
        print("Измерения завершены, построение графика...")
        
        # Отображаем график
        plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range)
        
    except KeyboardInterrupt:
        print("\nИзмерения прерваны пользователем")
        if voltage_values:  # Если есть данные, строим график
            print("Построение графика по собранным данным...")
            plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range if adc else 3.3)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        # Вызываем деструктор
        if adc is not None:
            adc.__del__()
        print("Программа завершена, ресурсы освобождены")