psql -p 5432 -At -F',' -c " SELECT
    name,
    CASE
        WHEN unit IN ('8kB', 'kB', 'MB', 'GB')
            THEN pg_size_pretty(
                CASE
                    WHEN unit = '8kB' THEN setting::bigint * 8192
                    WHEN unit = 'kB'  THEN setting::bigint * 1024
                    WHEN unit = 'MB'  THEN setting::bigint * 1024 * 1024
                    WHEN unit = 'GB'  THEN setting::bigint * 1024 * 1024 * 1024
                END
            )
        ELSE setting
    END AS value
FROM pg_settings
WHERE name IN (
  'work_mem',
  'maintenance_work_mem',
  'shared_buffers',
  'effective_cache_size',
  'temp_buffers',
  'random_page_cost',
  'seq_page_cost',
  'cpu_tuple_cost',
  'cpu_index_tuple_cost',
  'cpu_operator_cost',
  'parallel_setup_cost',
  'parallel_tuple_cost',
  'enable_nestloop',
  'enable_hashjoin',
  'enable_mergejoin',
  'enable_seqscan',
  'enable_indexscan',
  'enable_bitmapscan',
  'enable_indexonlyscan',
  'max_parallel_workers',
  'max_parallel_workers_per_gather',
  'max_worker_processes',
  'min_parallel_index_scan_size',
  'min_parallel_table_scan_size',
  'default_statistics_target',
  'constraint_exclusion',
  'from_collapse_limit',
  'join_collapse_limit',
  'geqo',
  'geqo_threshold',
  'effective_io_concurrency',
  'jit',
  'jit_above_cost'
)
ORDER BY name;
" > pg_config_snapshot.csv