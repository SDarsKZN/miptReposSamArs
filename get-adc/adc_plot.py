import RPi.GPIO as GPIO
import time
import matplotlib.pyplot as plt

class R2R_ADC:
    def __init__(self, dynamic_range, compare_time=0.001, verbose=False):  # Уменьшили задержку
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
    
    def fast_sequential_adc(self):
        """Быстрый последовательный АЦП с одним проходом"""
        max_value = 255
        
        for number in range(max_value + 1):
            self.number_to_dac(number)
            time.sleep(self.compare_time)  # Короткая задержка
            
            if GPIO.input(self.comp_gpio) == 1:
                return number
        
        return max_value
    
    def binary_search_adc(self):
        """Быстрый АЦП с бинарным поиском"""
        low = 0
        high = 255
        result = 0
        
        for _ in range(8):  # 8 итераций для 8-битного ЦАП
            mid = (low + high) // 2
            self.number_to_dac(mid)
            time.sleep(self.compare_time)
            
            if GPIO.input(self.comp_gpio) == 1:
                # U_DAC > U_ADC - уменьшаем напряжение
                high = mid - 1
                result = mid
            else:
                # U_DAC < U_ADC - увеличиваем напряжение
                low = mid + 1
                result = mid
        
        return result
    
    def get_sc_voltage(self, method='fast'):
        """Возвращает измеренное напряжение в Вольтах"""
        if method == 'fast':
            digital_value = self.fast_sequential_adc()
        else:
            digital_value = self.binary_search_adc()
            
        voltage = (digital_value / 255) * self.dynamic_range
        return voltage


def plot_voltage_vs_time(time_data, voltage_data, max_voltage):
    """Строит график зависимости напряжения от времени"""
    plt.figure(figsize=(12, 6))
    plt.plot(time_data, voltage_data, 'b-', linewidth=1, marker='.', markersize=2, label='Измеренное напряжение')
    plt.title('Зависимость напряжения от времени')
    plt.xlabel('Время, с')
    plt.ylabel('Напряжение, В')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.ylim(0, max_voltage * 1.1)
    if time_data:
        plt.xlim(0, max(time_data))
    plt.legend()
    plt.tight_layout()
    plt.show()


# Основной скрипт для измерения напряжения
if __name__ == "__main__":
    voltage_values = []
    time_values = []
    duration = 10.0  # Увеличиваем длительность измерений
    
    adc = None
    try:
        # Создаем объект ADC
        adc = R2R_ADC(dynamic_range=3.3, compare_time=0.001, verbose=False)
        
        start_time = time.time()
        measurement_count = 0
        
        print(f"Начало измерений на {duration} секунд...")
        print("Используется быстрый алгоритм АЦП")
        
        while (time.time() - start_time) < duration:
            current_time = time.time() - start_time
            
            # Используем быстрый метод
            voltage = adc.get_sc_voltage(method='fast')
            
            voltage_values.append(voltage)
            time_values.append(current_time)
            measurement_count += 1
            
            if measurement_count % 10 == 0:  # Выводим каждое 10-е измерение
                print(f"Время: {current_time:.2f} с, Напряжение: {voltage:.2f} В, Измерений: {measurement_count}")
            
            # Уменьшаем задержку между измерениями
            time.sleep(0.02)
        
        print(f"\nИзмерения завершены! Всего измерений: {measurement_count}")
        print(f"Частота измерений: {measurement_count/duration:.1f} Гц")
        
        # Отображаем график
        plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range)
        
    except KeyboardInterrupt:
        print(f"\nИзмерения прерваны пользователем. Всего измерений: {len(voltage_values)}")
        if voltage_values:
            print("Построение графика по собранным данным...")
            plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range if adc else 3.3)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        # Вызываем деструктор
        if adc is not None:
            adc.__del__()
        print("Программа завершена, ресурсы освобождены")