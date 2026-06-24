from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    USER = "user"


class LeadStatus(StrEnum):
    NOVO = "novo"
    A_CONTATAR = "a_contatar"
    CONTATADO = "contatado"
    NAO_RESPONDEU = "nao_respondeu"
    INTERESSADO = "interessado"
    PROPOSTA_ENVIADA = "proposta_enviada"
    FECHADO = "fechado"
    PERDIDO = "perdido"
    NAO_CONTATAR = "nao_contatar"


class DigitalPresence(StrEnum):
    SEM_SITE = "sem_site"
    SITE_RUIM = "site_ruim"
    SITE_OK = "site_ok"
    SITE_DESCONHECIDO = "site_desconhecido"


class PotentialLevel(StrEnum):
    BAIXO = "baixo"
    MEDIO = "medio"
    ALTO = "alto"


class SearchJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    REQUIRES_MANUAL_REVIEW = "requires_manual_review"


class SearchResultAction(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    DUPLICATE = "duplicate"
    SKIPPED = "skipped"
    FAILED = "failed"


class LeadEventType(StrEnum):
    NOTE = "note"
    STATUS_CHANGE = "status_change"
    CONTACT_ATTEMPT = "contact_attempt"
    MANUAL_UPDATE = "manual_update"


class SiteAnalysisStatus(StrEnum):
    SEM_SITE = "sem_site"
    SITE_RUIM = "site_ruim"
    SITE_OK = "site_ok"
    ERRO = "erro"
