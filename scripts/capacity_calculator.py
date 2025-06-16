#!/usr/bin/env python3
"""
Capacity Calculator for Observer AI Platform
Estimates required resources for target user loads
"""

import argparse
import math

class CapacityCalculator:
    def __init__(self):
        # Base resource requirements per service
        self.base_resources = {
            "backend_pod": {"cpu": 0.5, "memory": 1.0},  # CPU cores, Memory GB
            "frontend_pod": {"cpu": 0.25, "memory": 0.5},
            "mongodb_pod": {"cpu": 1.0, "memory": 2.0},
            "redis_pod": {"cpu": 0.5, "memory": 1.0},
        }
        
        # Performance assumptions
        self.performance_metrics = {
            "users_per_backend_pod": 100,
            "requests_per_user_per_minute": 10,
            "database_connections_per_pod": 20,
            "redis_ops_per_second": 10000,
        }
        
        # Safety factors
        self.safety_factors = {
            "cpu_overhead": 1.3,  # 30% overhead for system processes
            "memory_overhead": 1.2,  # 20% memory overhead
            "peak_load_factor": 2.0,  # Handle 2x expected load
        }
    
    def calculate_backend_pods(self, target_users):
        """Calculate required backend pods"""
        base_pods = math.ceil(target_users / self.performance_metrics["users_per_backend_pod"])
        
        # Apply safety factor for peak loads
        return math.ceil(base_pods * self.safety_factors["peak_load_factor"])
    
    def calculate_frontend_pods(self, backend_pods):
        """Calculate required frontend pods (usually fewer than backend)"""
        return max(2, math.ceil(backend_pods / 2))
    
    def calculate_database_pods(self, target_users):
        """Calculate required database pods"""
        # MongoDB: Start with 3 for replica set, scale up for very high loads
        mongodb_pods = 3 if target_users < 5000 else 5
        
        # Redis: Usually 1 is enough, 2 for redundancy at high scale
        redis_pods = 1 if target_users < 10000 else 2
        
        return mongodb_pods, redis_pods
    
    def calculate_total_resources(self, target_users):
        """Calculate total resource requirements"""
        backend_pods = self.calculate_backend_pods(target_users)
        frontend_pods = self.calculate_frontend_pods(backend_pods)
        mongodb_pods, redis_pods = self.calculate_database_pods(target_users)
        
        # Calculate CPU requirements
        total_cpu = (
            backend_pods * self.base_resources["backend_pod"]["cpu"] +
            frontend_pods * self.base_resources["frontend_pod"]["cpu"] +
            mongodb_pods * self.base_resources["mongodb_pod"]["cpu"] +
            redis_pods * self.base_resources["redis_pod"]["cpu"]
        )
        
        # Calculate memory requirements
        total_memory = (
            backend_pods * self.base_resources["backend_pod"]["memory"] +
            frontend_pods * self.base_resources["frontend_pod"]["memory"] +
            mongodb_pods * self.base_resources["mongodb_pod"]["memory"] +
            redis_pods * self.base_resources["redis_pod"]["memory"]
        )
        
        # Apply overhead factors
        total_cpu *= self.safety_factors["cpu_overhead"]
        total_memory *= self.safety_factors["memory_overhead"]
        
        return {
            "target_users": target_users,
            "pods": {
                "backend": backend_pods,
                "frontend": frontend_pods,
                "mongodb": mongodb_pods,
                "redis": redis_pods,
                "total": backend_pods + frontend_pods + mongodb_pods + redis_pods
            },
            "resources": {
                "total_cpu_cores": math.ceil(total_cpu),
                "total_memory_gb": math.ceil(total_memory),
                "estimated_nodes_needed": math.ceil(total_cpu / 4),  # Assuming 4 CPU per node
            },
            "estimated_costs": self.estimate_costs(total_cpu, total_memory)
        }
    
    def estimate_costs(self, cpu_cores, memory_gb):
        """Estimate monthly cloud costs"""
        # Rough estimates for major cloud providers (per month)
        aws_cost_per_cpu_hour = 0.0464  # t3.medium equivalent
        aws_cost_per_gb_hour = 0.0058
        
        monthly_hours = 24 * 30
        
        cpu_cost = cpu_cores * aws_cost_per_cpu_hour * monthly_hours
        memory_cost = memory_gb * aws_cost_per_gb_hour * monthly_hours
        
        # Add storage and networking costs (rough estimate)
        storage_cost = 50  # $50/month for storage
        networking_cost = 30  # $30/month for data transfer
        
        total_cost = cpu_cost + memory_cost + storage_cost + networking_cost
        
        return {
            "monthly_compute_cost": round(cpu_cost + memory_cost, 2),
            "monthly_storage_cost": storage_cost,
            "monthly_networking_cost": networking_cost,
            "total_monthly_cost": round(total_cost, 2)
        }
    
    def generate_recommendations(self, target_users):
        """Generate scaling recommendations"""
        capacity = self.calculate_total_resources(target_users)
        
        recommendations = []
        
        # Auto-scaling recommendations
        if target_users > 1000:
            recommendations.append("Enable Horizontal Pod Autoscaler (HPA) for automatic scaling")
            recommendations.append("Set up cluster autoscaling for node management")
        
        # Database recommendations
        if target_users > 5000:
            recommendations.append("Consider MongoDB sharding for horizontal database scaling")
            recommendations.append("Implement read replicas for database load distribution")
        
        # Caching recommendations
        if target_users > 2000:
            recommendations.append("Implement Redis clustering for cache scalability")
            recommendations.append("Add CDN for static asset delivery")
        
        # Monitoring recommendations
        recommendations.append("Set up comprehensive monitoring with Prometheus and Grafana")
        recommendations.append("Configure alerts for high CPU, memory, and error rates")
        
        # Performance recommendations
        if target_users > 10000:
            recommendations.append("Consider implementing database connection pooling")
            recommendations.append("Add load balancing across multiple regions")
            recommendations.append("Implement circuit breakers for external API calls")
        
        return recommendations
    
    def print_capacity_report(self, target_users):
        """Print comprehensive capacity report"""
        capacity = self.calculate_total_resources(target_users)
        recommendations = self.generate_recommendations(target_users)
        
        print("\n" + "="*80)
        print(f"OBSERVER AI CAPACITY PLANNING REPORT")
        print("="*80)
        print(f"Target Concurrent Users: {target_users:,}")
        print(f"Expected Peak Load: {int(target_users * self.safety_factors['peak_load_factor']):,} users")
        
        print("\n📊 REQUIRED INFRASTRUCTURE:")
        print("-"*40)
        print(f"Backend Pods:     {capacity['pods']['backend']:2d}")
        print(f"Frontend Pods:    {capacity['pods']['frontend']:2d}")
        print(f"MongoDB Pods:     {capacity['pods']['mongodb']:2d}")
        print(f"Redis Pods:       {capacity['pods']['redis']:2d}")
        print(f"Total Pods:       {capacity['pods']['total']:2d}")
        
        print("\n💻 RESOURCE REQUIREMENTS:")
        print("-"*40)
        print(f"Total CPU Cores:  {capacity['resources']['total_cpu_cores']:2d}")
        print(f"Total Memory:     {capacity['resources']['total_memory_gb']:2d} GB")
        print(f"Estimated Nodes:  {capacity['resources']['estimated_nodes_needed']:2d}")
        
        print("\n💰 ESTIMATED MONTHLY COSTS:")
        print("-"*40)
        costs = capacity['estimated_costs']
        print(f"Compute Cost:     ${costs['monthly_compute_cost']:8.2f}")
        print(f"Storage Cost:     ${costs['monthly_storage_cost']:8.2f}")
        print(f"Networking Cost:  ${costs['monthly_networking_cost']:8.2f}")
        print(f"TOTAL COST:       ${costs['total_monthly_cost']:8.2f}")
        
        print("\n🎯 PERFORMANCE EXPECTATIONS:")
        print("-"*40)
        expected_rps = target_users * self.performance_metrics["requests_per_user_per_minute"] / 60
        print(f"Expected Requests/Second: {expected_rps:,.0f}")
        print(f"Database Connections:     {capacity['pods']['backend'] * self.performance_metrics['database_connections_per_pod']}")
        print(f"Cache Operations/Second:  {self.performance_metrics['redis_ops_per_second']:,}")
        
        print("\n🚀 SCALING RECOMMENDATIONS:")
        print("-"*40)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i:2d}. {rec}")
        
        print("\n⚠️  IMPORTANT NOTES:")
        print("-"*40)
        print("• These estimates include safety factors for peak load handling")
        print("• Actual resource usage may vary based on user behavior patterns")
        print("• Consider implementing auto-scaling for cost optimization")
        print("• Monitor actual performance and adjust scaling policies accordingly")
        print("• Database costs may increase significantly with data growth")
        
        print("\n" + "="*80)

def main():
    parser = argparse.ArgumentParser(description="Calculate capacity requirements for Observer AI")
    parser.add_argument("users", type=int, help="Target number of concurrent users")
    parser.add_argument("--detailed", action="store_true", help="Show detailed breakdown")
    
    args = parser.parse_args()
    
    calculator = CapacityCalculator()
    
    if args.detailed:
        calculator.print_capacity_report(args.users)
    else:
        capacity = calculator.calculate_total_resources(args.users)
        print(f"\nFor {args.users:,} concurrent users:")
        print(f"Required: {capacity['pods']['total']} pods, {capacity['resources']['total_cpu_cores']} CPU cores, {capacity['resources']['total_memory_gb']} GB RAM")
        print(f"Estimated cost: ${capacity['estimated_costs']['total_monthly_cost']:.2f}/month")

if __name__ == "__main__":
    main()