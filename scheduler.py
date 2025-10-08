import schedule
from backup_logic import BackupLogic

class Scheduler:
    """
    Gerencia o agendamento de backups automáticos.
    """
    def __init__(self, backup_logic: BackupLogic, initial_schedules: list):
        self.backup_logic = backup_logic
        self.update_schedules(initial_schedules)

    def _run_scheduled_backup(self):
        """
        Método interno que será chamado pelo agendador.
        """
        print("Iniciando backup agendado...")
        # A lógica de backup já imprime seus próprios logs, então não precisamos capturar o resultado aqui.
        self.backup_logic.perform_backup()
        print("Backup agendado concluído.")

    def update_schedules(self, new_schedules: list):
        """
        Limpa todos os agendamentos existentes e cria novos com base na lista fornecida.
        """
        schedule.clear()
        print(f"Atualizando agendamentos para: {new_schedules}")
        
        for time_str in new_schedules:
            try:
                schedule.every().day.at(time_str).do(self._run_scheduled_backup)
            except Exception as e:
                print(f"Erro ao tentar agendar o horário '{time_str}': {e}")
        
        job_count = len(schedule.get_jobs())
        print(f"{job_count} jobs agendados.")

