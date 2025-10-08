import schedule
import time
from threading import Event

class Scheduler:
    """
    Gerencia o agendamento de backups automáticos. Roda em uma thread separada.
    """
    def __init__(self, backup_logic_instance, initial_schedules):
        self.backup_logic = backup_logic_instance
        self.stop_run_event = Event()
        self.update_schedules(initial_schedules)

    def update_schedules(self, new_schedules):
        """Limpa os agendamentos antigos e define novos."""
        schedule.clear()
        print(f"Atualizando agendamentos para: {new_schedules}")
        for t in new_schedules:
            try:
                schedule.every().day.at(t).do(self.job)
            except schedule.ScheduleValueError:
                print(f"Formato de hora inválido para o agendamento: '{t}'. Use HH:MM.")
        print(f"{len(schedule.get_jobs())} jobs agendados.")

    def job(self):
        """A tarefa que será executada pelo agendador."""
        print(f"Executando backup agendado...")
        self.backup_logic.perform_backup()
        print("Backup agendado concluído.")

    def run(self):
        """
        Inicia o loop do agendador. Este método deve ser o alvo da thread.
        """
        print("Agendador iniciado.")
        while not self.stop_run_event.is_set():
            schedule.run_pending()
            time.sleep(1) # Espera 1 segundo entre as verificações
        print("Agendador parado.")

    def stop(self):
        """Sinaliza para a thread do agendador parar."""
        self.stop_run_event.set()

