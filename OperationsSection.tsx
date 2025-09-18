import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Settings, Factory, Truck, Zap, Clock } from "lucide-react";
import { dashboardData } from "@/data/dashboardData";
import { Badge } from "@/components/ui/badge";

const UtilizationGauge = ({ 
  title, 
  value, 
  icon, 
  color = "primary" 
}: {
  title: string;
  value: number;
  icon: React.ReactNode;
  color?: string;
}) => {
  const getColorClass = () => {
    if (value >= 85 && value <= 95) return "text-green-500";
    if (value >= 75 && value < 85) return "text-orange-500";
    return "text-red-500";
  };

  const getGaugeColor = () => {
    if (value >= 85 && value <= 95) return "#10b981"; // green
    if (value >= 75 && value < 85) return "#f59e0b"; // orange
    return "#ef4444"; // red
  };

  // SVG semicircle gauge; value 0–100
  const rotation = (value / 100) * 180;

  return (
    <Card className="gauge-container">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {icon}
          <h3 className="font-semibold text-sm">{title}</h3>
        </div>
        <Badge variant="outline" className={getColorClass()}>
          {value}%
        </Badge>
      </div>
      
      {/* Gauge */}
      <div className="relative flex items-center justify-center py-4">
        {(() => {
          const size = 220; // px
          const r = 90; // radius
          const cx = size / 2;
          const cy = size / 2;
          const theta = Math.PI - (value / 100) * Math.PI; // left->right sweep
          const endX = cx + r * Math.cos(theta);
          const endY = cy - r * Math.sin(theta);
          const largeArc = value > 50 ? 1 : 0;
          const pathBg = `M ${cx - r} ${cy} A ${r} ${r} 0 1 1 ${cx + r} ${cy}`; // full top semicircle
          const pathVal = `M ${cx - r} ${cy} A ${r} ${r} 0 ${largeArc} 1 ${endX} ${endY}`;

          return (
            <svg width={size} height={size / 2} viewBox={`0 0 ${size} ${size / 2}`} aria-label={`${title} ${value}%`}>
              {/* background arc */}
              <path d={pathBg} fill="none" stroke="hsl(var(--muted))" strokeWidth={16} strokeLinecap="round" />
              {/* value arc */}
              <path d={pathVal} fill="none" stroke={getGaugeColor()} strokeWidth={16} strokeLinecap="round" />
              {/* indicator dot */}
              <circle cx={endX} cy={endY} r={6} fill={getGaugeColor()} />
              {/* center value */}
              <text x={cx} y={cy - 4} textAnchor="middle" style={{fontWeight:700, fontSize: 24, fill: getGaugeColor()}}>
                {value}%
              </text>
            </svg>
          );
        })()}
      </div>

    </Card>
  );
};

export function OperationsSection() {
  const insights = [
    {
      icon: <Factory className="w-5 h-5 text-blue-500" />,
      title: "Cube Utilization Maintained",
      description: "Kept utilization in optimal 85-90% range for efficiency"
    },
    {
      icon: <Truck className="w-5 h-5 text-green-500" />,
      title: "Reduced Overflow",
      description: "Minimized capacity overflow events through better planning"
    },
    {
      icon: <Clock className="w-5 h-5 text-purple-500" />,
      title: "SMED Implementation",
      description: "Reduced changeover time through Single Minute Exchange of Die techniques"
    },
    {
      icon: <Zap className="w-5 h-5 text-orange-500" />,
      title: "Process Optimization",
      description: "Streamlined operations for consistent throughput"
    }
  ];

  return (
    <section className="py-12 bg-secondary/30">
      <div className="container mx-auto px-6">
        <div className="section-header">
          <Settings className="w-8 h-8 text-primary" />
          <h2 className="section-title">Operations Excellence</h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Utilization Gauges */}
          <Card className="dashboard-section">
            <CardHeader>
              <CardTitle>Warehouse Utilization</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <UtilizationGauge
                  title="Inbound"
                  value={dashboardData.inbound_utilization_pct}
                  icon={<Truck className="w-5 h-5 text-blue-500" />}
                />
                <UtilizationGauge
                  title="Outbound"
                  value={dashboardData.outbound_utilization_pct}
                  icon={<Factory className="w-5 h-5 text-green-500" />}
                />
              </div>
              
              <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <h4 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">Utilization Analysis</h4>
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  Both inbound ({dashboardData.inbound_utilization_pct}%) and outbound ({dashboardData.outbound_utilization_pct}%) 
                  utilization are in the optimal 85-90% range, indicating efficient capacity management without bottlenecks.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Operational Improvements */}
          <Card className="dashboard-section">
            <CardHeader>
              <CardTitle>Operational Improvements</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {insights.map((insight, index) => (
                  <div key={index} className="flex items-start gap-4 p-4 rounded-lg bg-card border border-border/20">
                    <div className="flex-shrink-0 mt-0.5">
                      {insight.icon}
                    </div>
                    <div>
                      <h4 className="font-semibold mb-1">{insight.title}</h4>
                      <p className="text-sm text-muted-foreground">{insight.description}</p>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-6 grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-muted/30 rounded-lg">
                  <p className="text-sm text-muted-foreground mb-1">Average Utilization</p>
                  <p className="text-xl font-bold text-primary">
                    {((dashboardData.inbound_utilization_pct + dashboardData.outbound_utilization_pct) / 2).toFixed(1)}%
                  </p>
                </div>
                <div className="text-center p-4 bg-muted/30 rounded-lg">
                  <p className="text-sm text-muted-foreground mb-1">Efficiency Target</p>
                  <p className="text-xl font-bold text-green-600">✓ Achieved</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}
