import smbus
import time

class MCP3021:
    def __init__(self, dynamic_range, verbose=False):
        """
        Конструктор класса MCP3021
        
        Args:
            dynamic_range (float): Динамический диапазон АЦП в Вольтах
            verbose (bool): Флаг отладочного вывода
        """
        self.bus = smbus.SMBus(1)  # Используем I2C шину 1
        self.dynamic_range = dynamic_range
        self.address = 0x4D  # Адрес MCP3021 по умолчанию
        self.verbose = verbose
        
        if self.verbose:
            print(f"MCP3021 инициализирован:")
            print(f"  Адрес: 0x{self.address:02X}")
            print(f"  Динамический диапазон: {self.dynamic_range} В")
            print(f"  Шина I2C: 1")
    
    def deinit(self):
        """Деструктор - освобождает шину I2C"""
        self.bus.close()
        if self.verbose:
            print("Шина I2C освобождена")
    
    def get_number(self):
        """
        Читает число из микросхемы MCP3021
        
        Returns:
            int: 10-битное число (0-1023)
        """
        try:
            # 1. Прочитайте два байта из устройства по его адресу
            data = self.bus.read_word_data(self.address, 0)
            
            # 2. Выделите из прочитанного числа байт, который пришёл по шине вторым (lower)
            lower_data_byte = data & 0xFF
            
            # 3. Выделите из прочитанного числа байт, который пришёл по шине первым (upper)  
            upper_data_byte = (data >> 8) & 0xFF
            
            # 4. Выделите из двух прочитанных байт число, переданное микросхемой
            # Формат данных MCP3021: [XXXX XXDD DDDD DDDD] где D - биты данных
            number = ((upper_data_byte & 0x0F) << 6) | (lower_data_byte >> 2)
            
            # 5. Распечатайте данные, байты и число, если задан явный вывод отладочной информации
            if self.verbose:
                print(f"Принятые данные: 0x{data:04X}")
                print(f"  Старший байт: 0x{upper_data_byte:02X} ({upper_data_byte:08b})")
                print(f"  Младший байт: 0x{lower_data_byte:02X} ({lower_data_byte:08b})")
                print(f"  Число (10 бит): {number} ({number:010b})")
            
            # 6. Верните прочитанное из микросхемы число
            return number
            
        except Exception as e:
            if self.verbose:
                print(f"Ошибка чтения MCP3021: {e}")
            return 0
    
    def get_voltage(self):
        """
        Возвращает измеренное микросхемой MCP3021 напряжение в Вольтах
        
        Returns:
            float: Напряжение в Вольтах
        """
        number = self.get_number()
        # Преобразуем 10-битное число в напряжение
        voltage = (number / 1023.0) * self.dynamic_range
        return voltage


# Основной охранник
if __name__ == "__main__":
    mcp = None
    try:
        # 1. Создайте объект класса MCP3021
        # ЗАМЕНИТЕ 5.0 на реально измеренное напряжение на контакте PWR блока AUX!
        DYNAMIC_RANGE = 5.0  # Напряжение питания АЦП (обычно 5V или 3.3V)
        
        print("=== MCP3021 10-битный АЦП ===")
        print(f"Динамический диапазон: {DYNAMIC_RANGE} В")
        print("Для остановки нажмите Ctrl+C\n")
        
        mcp = MCP3021(dynamic_range=DYNAMIC_RANGE, verbose=False)
        
        measurement_count = 0
        
        # 2. В бесконечном цикле делайте три действия:
        while True:
            # 2.1. Читайте напряжение
            voltage = mcp.get_voltage()
            measurement_count += 1
            
            # 2.2. Печатайте его в терминал
            print(f"Измерение {measurement_count}: Напряжение = {voltage:.3f} В")
            
            # 2.3. Ждите 1 с, чтобы не перегружать вывод терминала
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\nИзмерения остановлены пользователем")
        print(f"Всего выполнено измерений: {measurement_count}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        # 3. Вызовите «деструктор» объекта класса MCP3021
        if mcp is not None:
            mcp.deinit()
        print("Программа завершена, ресурсы освобождены")