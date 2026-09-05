import React, { useEffect, useState } from 'react';
import { X, UserCheck, AlertTriangle, ShieldCheck, DollarSign, PackageCheck, Headphones, ArrowRight } from 'lucide-react';
import { api } from '../services/api';

interface Customer360ModalProps {
  customerId: string | null;
  onClose: () => void;
}

export const Customer360Modal: React.FC<Customer360ModalProps> = ({ customerId, onClose }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!customerId) return;
    setLoading(true);
    api.getCustomer360(customerId)
      .then((res) => setData(res))
      .catch((err) => console.error('Failed to load customer 360', err))
      .finally(() => setLoading(false));
  }, [customerId]);

  if (!customerId) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-blue-500/20 text-blue-400 border border-blue-500/30">
              <UserCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white">{data?.profile?.name || customerId}</h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  {customerId}
                </span>
              </div>
              <p className="text-xs text-slate-400">{data?.profile?.tier || 'Customer Account'} • {data?.profile?.city || 'Location N/A'}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="py-12 text-center text-xs text-slate-400">Loading Customer 360 profile...</div>
          ) : data ? (
            <>
              {/* Health Score & Key Metrics */}
              <div className="grid grid-cols-4 gap-4">
                <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60">
                  <span className="text-xs text-slate-400">Health Score</span>
                  <div className={`text-xl font-bold mt-1 ${
                    data.metrics.health_score >= 80 ? 'text-emerald-400' : 'text-amber-400'
                  }`}>
                    {data.metrics.health_score}%
                  </div>
                  <span className="text-[10px] text-slate-500 font-semibold">{data.metrics.risk_tier}</span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60">
                  <span className="text-xs text-slate-400">Total Spend</span>
                  <div className="text-xl font-bold text-cyan-400 mt-1">
                    ${data.metrics.total_spent.toLocaleString()}
                  </div>
                  <span className="text-[10px] text-slate-500">{data.metrics.total_orders} orders placed</span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60">
                  <span className="text-xs text-slate-400">Open Balance</span>
                  <div className="text-xl font-bold text-rose-400 mt-1">
                    ${data.metrics.open_invoices_balance.toLocaleString()}
                  </div>
                  <span className="text-[10px] text-slate-500">{data.metrics.overdue_invoices} overdue invoices</span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60">
                  <span className="text-xs text-slate-400">Support Tickets</span>
                  <div className="text-xl font-bold text-amber-400 mt-1">{data.metrics.open_tickets}</div>
                  <span className="text-[10px] text-slate-500">{data.metrics.breached_tickets} breached SLA</span>
                </div>
              </div>

              {/* Recommended Operational Next Steps */}
              <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 space-y-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Operational Actions</span>
                <ul className="space-y-1">
                  {data.recommended_actions?.map((act: string, i: number) => (
                    <li key={i} className="text-xs text-slate-300 flex items-center gap-2">
                      <ArrowRight className="w-3.5 h-3.5 text-blue-400" />
                      <span>{act}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Recent Orders List */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-300">Recent Orders</span>
                <div className="overflow-x-auto rounded-lg border border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-slate-400">
                      <tr>
                        <th className="p-2.5">Order ID</th>
                        <th className="p-2.5">Date</th>
                        <th className="p-2.5">Status</th>
                        <th className="p-2.5 text-right">Amount</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {data.orders?.slice(0, 5).map((o: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-800/40 text-slate-300">
                          <td className="p-2.5 font-mono text-cyan-400">{o.order_id}</td>
                          <td className="p-2.5">{o.order_date?.split(' ')[0]}</td>
                          <td className="p-2.5">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                              o.status === 'Delayed' ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'
                            }`}>
                              {o.status}
                            </span>
                          </td>
                          <td className="p-2.5 text-right font-medium">${o.total_amount?.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            <div className="py-8 text-center text-xs text-slate-400">No profile details available.</div>
          )}
        </div>
      </div>
    </div>
  );
};
