import RPi.GPIO as GPIO
import time
import matplotlib.pyplot as plt

class R2R_ADC:
    def __init__(self, dynamic_range, compare_time=0.001, verbose=True):  # Включим verbose для отладки
        self.dynamic_range = dynamic_range
        self.verbose = verbose
        self.compare_time = compare_time
        
        # Проверим правильность пинов - это стандартные пины для R2R
        self.bits_gpio = [26, 20, 19, 16, 13, 12, 25, 11]
        self.comp_gpio = 21  # GPIO21 соответствует физическому пину 40

        print(f"Пины ЦАП: {self.bits_gpio}")
        print(f"Пин компаратора: {self.comp_gpio}")
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.bits_gpio, GPIO.OUT, initial=0)
        GPIO.setup(self.comp_gpio, GPIO.IN)
        
        # Протестируем компаратор
        print("Тестирование компаратора...")
        self.number_to_dac(0)  # Нулевое напряжение
        time.sleep(0.1)
        comp_state_low = GPIO.input(self.comp_gpio)
        
        self.number_to_dac(255)  # Максимальное напряжение  
        time.sleep(0.1)
        comp_state_high = GPIO.input(self.comp_gpio)
        
        print(f"Состояние компаратора (ЦАП=0): {comp_state_low}")
        print(f"Состояние компаратора (ЦАП=255): {comp_state_high}")
    
    def __del__(self):
        """Деструктор - выставляет 0 на выход ЦАП и очищает настройки GPIO"""
        GPIO.output(self.bits_gpio, 0)
        GPIO.cleanup()
    
    def number_to_dac(self, number):
        """Подает число number на вход ЦАП"""
        binary = format(number, '08b')
        for i, pin in enumerate(self.bits_gpio):
            GPIO.output(pin, int(binary[i]))
    
    def test_comparator(self):
        """Тестирует работу компаратора"""
        print("\nТестирование компаратора на разных значениях ЦАП:")
        test_values = [0, 64, 128, 192, 255]
        
        for val in test_values:
            self.number_to_dac(val)
            time.sleep(0.1)
            comp_state = GPIO.input(self.comp_gpio)
            voltage = (val / 255) * self.dynamic_range
            print(f"ЦАП={val:3d} ({voltage:.2f} В) -> Компаратор: {comp_state}")
    
    def fast_sequential_adc(self):
        """Быстрый последовательный АЦП"""
        if self.verbose:
            print("Начало измерения АЦП...")
            
        for number in range(256):
            self.number_to_dac(number)
            time.sleep(self.compare_time)
            
            comp_state = GPIO.input(self.comp_gpio)
            
            if self.verbose and number % 32 == 0:  # Выводим каждые 32 шага
                voltage = (number / 255) * self.dynamic_range
                print(f"Шаг {number:3d} ({voltage:.2f} В) -> Компаратор: {comp_state}")
            
            if comp_state == 1:
                if self.verbose:
                    print(f"Найден переход при числе: {number}")
                return number
        
        return 255
    
    def get_sc_voltage(self):
        """Возвращает измеренное напряжение в Вольтах"""
        digital_value = self.fast_sequential_adc()
        voltage = (digital_value / 255) * self.dynamic_range
        return voltage


def plot_voltage_vs_time(time_data, voltage_data, max_voltage):
    """Строит график зависимости напряжения от времени"""
    plt.figure(figsize=(12, 6))
    plt.plot(time_data, voltage_data, 'b-', linewidth=1, marker='o', markersize=3, label='Измеренное напряжение')
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


# Альтернативная версия с возможностью смены пинов
class R2R_ADC_Configurable:
    def __init__(self, dynamic_range, dac_pins=[26, 20, 19, 16, 13, 12, 25, 11], comp_pin=21, compare_time=0.001, verbose=True):
        self.dynamic_range = dynamic_range
        self.verbose = verbose
        self.compare_time = compare_time
        
        self.bits_gpio = dac_pins
        self.comp_gpio = comp_pin

        print(f"Пины ЦАП: {self.bits_gpio}")
        print(f"Пин компаратора: {self.comp_gpio}")
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.bits_gpio, GPIO.OUT, initial=0)
        GPIO.setup(self.comp_gpio, GPIO.IN)
        
        self.test_comparator()
    
    def __del__(self):
        GPIO.output(self.bits_gpio, 0)
        GPIO.cleanup()
    
    def number_to_dac(self, number):
        binary = format(number, '08b')
        for i, pin in enumerate(self.bits_gpio):
            GPIO.output(pin, int(binary[i]))
    
    def test_comparator(self):
        """Тестирует работу компаратора"""
        print("\n=== ТЕСТИРОВАНИЕ КОМПАРАТОРА ===")
        test_values = [0, 32, 64, 96, 128, 160, 192, 224, 255]
        
        for val in test_values:
            self.number_to_dac(val)
            time.sleep(0.1)  # Даем время на установление напряжения
            comp_state = GPIO.input(self.comp_gpio)
            voltage = (val / 255) * self.dynamic_range
            print(f"ЦАП={val:3d} ({voltage:.2f} В) -> Компаратор: {comp_state}")
        
        print("=== ТЕСТ ЗАВЕРШЕН ===\n")
    
    def fast_sequential_adc(self):
        for number in range(256):
            self.number_to_dac(number)
            time.sleep(self.compare_time)
            if GPIO.input(self.comp_gpio) == 1:
                return number
        return 255
    
    def get_sc_voltage(self):
        digital_value = self.fast_sequential_adc()
        voltage = (digital_value / 255) * self.dynamic_range
        return voltage


# Основной скрипт
if __name__ == "__main__":
    voltage_values = []
    time_values = []
    duration = 15.0  # Увеличиваем длительность
    
    adc = None
    try:
        print("=== ПРОВЕРКА ПОДКЛЮЧЕНИЯ ===")
        print("Физические пины на Raspberry Pi:")
        print("GPIO26 -> физический пин 37")
        print("GPIO20 -> физический пин 38") 
        print("GPIO21 -> физический пин 40 (компаратор)")
        print("Убедитесь, что компаратор подключен к правильному пину!\n")
        
        # Используем конфигурируемую версию
        adc = R2R_ADC_Configurable(dynamic_range=3.3, verbose=True)
        
        start_time = time.time()
        measurement_count = 0
        
        print("Начало измерений...")
        print("Меняйте входное напряжение на компараторе во время измерений!")
        
        while (time.time() - start_time) < duration:
            current_time = time.time() - start_time
            
            voltage = adc.get_sc_voltage()
            
            voltage_values.append(voltage)
            time_values.append(current_time)
            measurement_count += 1
            
            print(f"Измерение {measurement_count:3d}: Время {current_time:5.1f} с, Напряжение: {voltage:.2f} В")
            
            time.sleep(0.5)  # Измеряем каждые 0.5 секунды
        
        print(f"\nИзмерения завершены! Всего измерений: {measurement_count}")
        
        # Отображаем график
        plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range)
        
    except KeyboardInterrupt:
        print(f"\nИзмерения прерваны. Всего измерений: {len(voltage_values)}")
        if voltage_values:
            plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range if adc else 3.3)
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        if adc is not None:
            adc.__del__()
        print("Программа завершена")