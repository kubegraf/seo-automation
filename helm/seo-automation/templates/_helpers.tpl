{{/*
Expand the name of the chart.
*/}}
{{- define "seo-automation.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "seo-automation.fullname" -}}
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
Create chart label
*/}}
{{- define "seo-automation.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "seo-automation.labels" -}}
helm.sh/chart: {{ include "seo-automation.chart" . }}
{{ include "seo-automation.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "seo-automation.selectorLabels" -}}
app.kubernetes.io/name: {{ include "seo-automation.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Image name helper
*/}}
{{- define "seo-automation.image" -}}
{{- printf "%s/%s/seo-%s:%s" .Values.image.registry .Values.image.organization .service .Values.image.tag }}
{{- end }}

{{/*
Environment variables from ConfigMap and Secrets
*/}}
{{- define "seo-automation.envFrom" -}}
envFrom:
  - configMapRef:
      name: seo-automation-config
  - secretRef:
      name: seo-automation-secrets
{{- end }}
