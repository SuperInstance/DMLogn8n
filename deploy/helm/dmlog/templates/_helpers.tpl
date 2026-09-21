{{/*
Expand the name of the chart.
*/}}
{{- define "dmlog.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "dmlog.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "dmlog.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "dmlog.labels" -}}
helm.sh/chart: {{ include "dmlog.chart" . }}
{{ include "dmlog.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- if .Values.commonLabels }}
{{ toYaml .Values.commonLabels }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "dmlog.selectorLabels" -}}
app.kubernetes.io/name: {{ include "dmlog.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Values.podLabels }}
{{ toYaml .Values.podLabels }}
{{- end }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "dmlog.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "dmlog.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the image name
*/}}
{{- define "dmlog.image" -}}
{{- $registry := .Values.global.imageRegistry | default .Values.image.registry }}
{{- $repository := .Values.image.repository }}
{{- $tag := .Values.image.tag | default .Chart.AppVersion }}
{{- if .Values.global.imageRegistry }}
{{- printf "%s/%s:%s" $registry $repository $tag }}
{{- else }}
{{- printf "%s/%s:%s" $registry $repository $tag }}
{{- end }}
{{- end }}

{{/*
Create the database URL
*/}}
{{- define "dmlog.databaseURL" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "postgresql://%s:%s@%s:%s/%s" .Values.postgresql.auth.username .Values.postgresql.auth.password (include "dmlog.fullname" .) .Values.postgresql.primary.service.ports.postgresql .Values.postgresql.auth.database }}
{{- else }}
{{- .Values.config.database.url | default "postgresql://dmlog_user:dmlog_password@localhost:5432/dmlog_prod" }}
{{- end }}
{{- end }}

{{/*
Create the Redis URL
*/}}
{{- define "dmlog.redisURL" -}}
{{- if .Values.redis.enabled }}
{{- if .Values.redis.auth.enabled }}
{{- printf "redis://:%s@%s:%s/%s" .Values.redis.auth.password (include "dmlog.fullname" .)-master .Values.redis.master.service.ports.redis .Values.config.redis.db }}
{{- else }}
{{- printf "redis://%s:%s/%s" (include "dmlog.fullname" .)-master .Values.redis.master.service.ports.redis .Values.config.redis.db }}
{{- end }}
{{- else }}
{{- printf "redis://localhost:6379/%s" .Values.config.redis.db }}
{{- end }}
{{- end }}

{{/*
Create the Qdrant URL
*/}}
{{- define "dmlog.qdrantURL" -}}
{{- if .Values.qdrant.enabled }}
{{- printf "http://%s:%s" (include "dmlog.fullname" .)-qdrant .Values.qdrant.service.ports.http }}
{{- else }}
{{- .Values.config.qdrant.url | default "http://localhost:6333" }}
{{- end }}
{{- end }}

{{/*
Return the proper Docker Image Registry Secret Names
*/}}
{{- define "dmlog.imagePullSecrets" -}}
{{- include "common.images.pullSecrets" (dict "images" (list .Values.image) "global" .Values.global) -}}
{{- end }}

{{/*
Create a default fully qualified redis name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "dmlog.redis.fullname" -}}
{{- if .Values.redis.fullnameOverride -}}
{{- .Values.redis.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default "redis" .Values.redis.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end }}

{{/*
Return the proper Redis Secret Name
*/}}
{{- define "dmlog.redis.secretName" -}}
{{- if .Values.redis.auth.existingSecret -}}
{{- printf "%s" (tpl .Values.redis.auth.existingSecret $) -}}
{{- else -}}
{{- printf "%s" (include "dmlog.redis.fullname" .) -}}
{{- end -}}
{{- end }}

{{/*
Create a default fully qualified postgresql name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "dmlog.postgresql.fullname" -}}
{{- if .Values.postgresql.fullnameOverride -}}
{{- .Values.postgresql.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default "postgresql" .Values.postgresql.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end }}

{{/*
Return the proper PostgreSQL Secret Name
*/}}
{{- define "dmlog.postgresql.secretName" -}}
{{- if .Values.postgresql.auth.existingSecret -}}
{{- printf "%s" (tpl .Values.postgresql.auth.existingSecret $) -}}
{{- else -}}
{{- printf "%s" (include "dmlog.postgresql.fullname" .) -}}
{{- end -}}
{{- end }}

{{/*
Return the secret with DMLog credentials
*/}}
{{- define "dmlog.secretName" -}}
{{- if .Values.secrets.existingSecret -}}
{{- .Values.secrets.existingSecret -}}
{{- else -}}
{{- printf "%s" (include "dmlog.fullname" .) -}}
{{- end -}}
{{- end }}

{{/*
Return true if a secret object should be created
*/}}
{{- define "dmlog.createSecret" -}}
{{- if .Values.secrets.enabled -}}
{{- true -}}
{{- else if not .Values.secrets.existingSecret -}}
{{- true -}}
{{- end -}}
{{- end }}

{{/*
Compile all warnings into a single message, and call fail.
*/}}
{{- define "dmlog.validateValues.warnings" -}}
{{- $messages := list -}}
{{- $messages := append $messages (include "dmlog.validateValues.warning" .) -}}
{{- $messages := without $messages "" -}}
{{- $message := join "\n" $messages -}}
{{- if $message -}}
{{- printf "\nWARNINGS:\n%s" $message | fail -}}
{{- end -}}
{{- end }}

{{/*
Create a message for warnings
*/}}
{{- define "dmlog.validateValues.warning" -}}
{{- end -}}