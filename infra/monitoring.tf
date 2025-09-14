# Monitoring configuration for TruthLens

# Cloud Monitoring Dashboard
resource "google_monitoring_dashboard" "truthlens_dashboard" {
  dashboard_json = jsonencode({
    displayName = "TruthLens Monitoring Dashboard"
    mosaicLayout = {
      tiles = [
        {
          width  = 6
          height  = 4
          widget = {
            title = "Request Rate"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"truthlens-api\""
                      aggregation = {
                        alignmentPeriod    = "60s"
                        perSeriesAligner   = "ALIGN_RATE"
                        crossSeriesReducer = "REDUCE_SUM"
                        groupByFields      = ["resource.labels.service_name"]
                      }
                    }
                  }
                  plotType = "LINE"
                }
              ]
              timeshiftDuration = "0s"
              yAxis = {
                label = "requests/sec"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width  = 6
          height  = 4
          widget = {
            title = "P95 Latency"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"truthlens-api\" AND metric.type=\"run.googleapis.com/request_latencies\""
                      aggregation = {
                        alignmentPeriod    = "60s"
                        perSeriesAligner   = "ALIGN_DELTA"
                        crossSeriesReducer = "REDUCE_PERCENTILE_95"
                        groupByFields      = ["resource.labels.service_name"]
                      }
                    }
                  }
                  plotType = "LINE"
                }
              ]
              timeshiftDuration = "0s"
              yAxis = {
                label = "ms"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width  = 6
          height  = 4
          widget = {
            title = "Error Rate"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"truthlens-api\" AND metric.type=\"run.googleapis.com/request_count\""
                      aggregation = {
                        alignmentPeriod    = "60s"
                        perSeriesAligner   = "ALIGN_RATE"
                        crossSeriesReducer = "REDUCE_SUM"
                        groupByFields      = ["resource.labels.service_name"]
                      }
                    }
                  }
                  plotType = "LINE"
                }
              ]
              timeshiftDuration = "0s"
              yAxis = {
                label = "errors/sec"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width  = 6
          height  = 4
          widget = {
            title = "Cost per 1K Queries"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"truthlens-api\""
                      aggregation = {
                        alignmentPeriod    = "3600s"
                        perSeriesAligner   = "ALIGN_MEAN"
                        crossSeriesReducer = "REDUCE_MEAN"
                        groupByFields      = ["resource.labels.service_name"]
                      }
                    }
                  }
                  plotType = "LINE"
                }
              ]
              timeshiftDuration = "0s"
              yAxis = {
                label = "USD"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width  = 12
          height = 4
          widget = {
            title = "Verification Verdicts Distribution"
            pieChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "resource.type=\"bigquery_table\" AND resource.labels.dataset_id=\"truthlens_logs\""
                      aggregation = {
                        alignmentPeriod    = "3600s"
                        perSeriesAligner   = "ALIGN_RATE"
                        crossSeriesReducer = "REDUCE_SUM"
                        groupByFields      = ["metric.labels.verdict"]
                      }
                    }
                  }
                }
              ]
            }
          }
        }
      ]
    }
  })
}

# Alerting Policy for High Latency
resource "google_monitoring_alert_policy" "high_latency" {
  display_name = "TruthLens High Latency Alert"
  combiner     = "OR"
  conditions {
    display_name = "P95 Latency > 3s"
    condition_threshold {
      filter         = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"truthlens-api\" AND metric.type=\"run.googleapis.com/request_latencies\""
      duration       = "300s"
      comparison     = "COMPARISON_GREATER_THAN"
      threshold_value = 3000
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_PERCENTILE_95"
        group_by_fields = ["resource.labels.service_name"]
      }
    }
  }
  notification_channels = [google_monitoring_notification_channel.email.id]
}

# Alerting Policy for High Error Rate
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "TruthLens High Error Rate Alert"
  combiner     = "OR"
  conditions {
    display_name = "Error Rate > 2%"
    condition_threshold {
      filter         = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"truthlens-api\" AND metric.type=\"run.googleapis.com/request_count\""
      duration       = "300s"
      comparison     = "COMPARISON_GREATER_THAN"
      threshold_value = 0.02
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields = ["resource.labels.service_name"]
      }
    }
  }
  notification_channels = [google_monitoring_notification_channel.email.id]
}

# Email notification channel
resource "google_monitoring_notification_channel" "email" {
  display_name = "TruthLens Email Alerts"
  type         = "email"
  labels = {
    email_address = "alerts@truthlens.app"
  }
}

# Log-based metrics
resource "google_logging_metric" "verification_requests" {
  name   = "truthlens_verification_requests"
  filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"truthlens-api\" AND jsonPayload.message=\"Verification completed\""
  metric_descriptor {
    metric_kind = "COUNTER"
    value_type  = "INT64"
    display_name = "Verification Requests"
    description  = "Number of verification requests processed"
  }
}

resource "google_logging_metric" "verification_cost" {
  name   = "truthlens_verification_cost"
  filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"truthlens-api\" AND jsonPayload.cost_usd"
  metric_descriptor {
    metric_kind = "GAUGE"
    value_type  = "DOUBLE"
    display_name = "Verification Cost"
    description  = "Cost per verification request"
  }
  value_extractor = "EXTRACT(jsonPayload.cost_usd)"
}

# Uptime check
resource "google_monitoring_uptime_check_config" "truthlens_uptime" {
  display_name = "TruthLens API Uptime Check"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path         = "/healthz"
    port         = "443"
    request_method = "GET"
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = google_api_gateway_gateway.truthlens_gateway.default_hostname
    }
  }

  content_matchers {
    content = "healthy"
    matcher = "CONTAINS_STRING"
  }
}
