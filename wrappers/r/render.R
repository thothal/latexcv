`%||%` <- function(lhs, rhs) {
   if (is.null(lhs) || length(lhs) == 0 || is.na(lhs) || !nzchar(lhs)) {
      rhs
   } else {
      lhs
   }
}

quote_path <- function(path) {
   shQuote(normalizePath(path, winslash = "/", mustWork = FALSE))
}

find_cv_command <- function(python = NULL) {
   command <- Sys.which("cvrender")
   if (nzchar(command)) {
      return(list(command = command, module = NULL))
   }

   python <- python %||% Sys.getenv("CV_RENDER_PYTHON", unset = "")
   if (!nzchar(python)) {
      python <- Sys.getenv("RETICULATE_PYTHON", unset = "")
   }
   if (!nzchar(python)) {
      conda_prefix <- Sys.getenv("CONDA_PREFIX", unset = "")
      if (nzchar(conda_prefix)) {
         python <- file.path(conda_prefix, "python.exe")
      }
   }
   if (!nzchar(python)) {
      python <- Sys.which("python")
   }
   if (!nzchar(python)) {
      stop("Could not find either 'cvrender' or a usable Python executable.", call. = FALSE)
   }

   list(command = python, module = "latexcv.cli")
}

render_cv <- function(
   profile = "full-showcase",
    repo_root = getwd(),
    lang = c("de", "en"),
    data_dir = NULL,
    output_dir = NULL,
    tex_only = FALSE,
    cleanup = TRUE,
    format_output = FALSE,
    command = NULL,
    python = NULL,
    ...) {
   lang <- match.arg(lang)

   profile_dir <- file.path(repo_root, "examples", profile)
   data_dir <- quote_path(data_dir %||% file.path(profile_dir, "data"))
   output_dir <- quote_path(output_dir %||% file.path(profile_dir, "output"))

   args <- c(
      data_dir,
      "--output-dir", output_dir,
      "--lang", lang
   )

   if (tex_only) {
      args <- c(args, "--tex-only")
   }
   if (!cleanup) {
      args <- c(args, "--no-cleanup")
   }
   if (format_output) {
      args <- c(args, "--format-output")
   }

   extra_args <- list(...)
   if (length(extra_args) > 0) {
      args <- c(args, unlist(extra_args, use.names = FALSE))
   }

   if (!is.null(command) && nzchar(command)) {
      resolved <- list(command = command, module = NULL)
   } else {
      resolved <- find_cv_command(python = python)
   }

   if (!is.null(resolved$module)) {
      args <- c("-m", resolved$module, args)
   }

   output <- system2(resolved$command, args = args, stdout = TRUE, stderr = TRUE)
   status <- attr(output, "status")
   if (!is.null(status) && status != 0) {
      stop(paste(output, collapse = "\n"), call. = FALSE)
   }

   invisible(tail(output, 1L))
}
