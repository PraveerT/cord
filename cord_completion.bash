#!/bin/bash
# Bash completion for cord command

_cord_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Available commands
    opts="show cpu memory mem disk processes proc network net info kill help"

    # Handle different cases
    case "${prev}" in
        cord)
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            return 0
            ;;
        kill)
            # For kill command, suggest running process PIDs
            local pids=$(ps -eo pid --no-headers | tr -d ' ')
            COMPREPLY=( $(compgen -W "${pids}" -- ${cur}) )
            return 0
            ;;
        *)
            ;;
    esac

    # Default completion
    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
}

# Register the completion function
complete -F _cord_completion cord