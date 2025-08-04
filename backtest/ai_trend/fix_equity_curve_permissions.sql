-- Fix permissions for equity_curve table and sequence
-- This script resolves the "permission denied for sequence equity_curve_id_seq" error

-- Grant permissions on the equity_curve table
GRANT ALL PRIVILEGES ON TABLE ai_trend_analysis.equity_curve TO postgres;
GRANT ALL PRIVILEGES ON TABLE ai_trend_analysis.equity_curve TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE ai_trend_analysis.equity_curve TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE ai_trend_analysis.equity_curve TO authenticated;

-- Grant permissions on the sequence (this fixes the main error)
GRANT ALL PRIVILEGES ON SEQUENCE ai_trend_analysis.equity_curve_id_seq TO postgres;
GRANT ALL PRIVILEGES ON SEQUENCE ai_trend_analysis.equity_curve_id_seq TO service_role;
GRANT USAGE, SELECT ON SEQUENCE ai_trend_analysis.equity_curve_id_seq TO anon;
GRANT USAGE, SELECT ON SEQUENCE ai_trend_analysis.equity_curve_id_seq TO authenticated;

-- Grant permissions on the views
GRANT SELECT ON ai_trend_analysis.latest_equity_curves TO postgres;
GRANT SELECT ON ai_trend_analysis.latest_equity_curves TO service_role;
GRANT SELECT ON ai_trend_analysis.latest_equity_curves TO anon;
GRANT SELECT ON ai_trend_analysis.latest_equity_curves TO authenticated;

GRANT SELECT ON ai_trend_analysis.equity_curve_summary TO postgres;
GRANT SELECT ON ai_trend_analysis.equity_curve_summary TO service_role;
GRANT SELECT ON ai_trend_analysis.equity_curve_summary TO anon;
GRANT SELECT ON ai_trend_analysis.equity_curve_summary TO authenticated;

-- Enable Row Level Security (if not already enabled)
ALTER TABLE ai_trend_analysis.equity_curve ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for equity_curve table
-- Policy for service_role (full access)
CREATE POLICY "service_role_all_equity_curve" ON ai_trend_analysis.equity_curve
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Policy for authenticated users (full access)
CREATE POLICY "authenticated_all_equity_curve" ON ai_trend_analysis.equity_curve
    FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- Policy for anonymous users (read-only)
CREATE POLICY "anon_select_equity_curve" ON ai_trend_analysis.equity_curve
    FOR SELECT TO anon USING (true);

-- Verify permissions (optional - can be commented out)
-- SELECT 
--     schemaname, 
--     tablename, 
--     tableowner, 
--     hasinserts, 
--     hasselects, 
--     hasupdates, 
--     hasdeletes 
-- FROM pg_tables 
-- WHERE schemaname = 'ai_trend_analysis' AND tablename = 'equity_curve';

COMMIT; 